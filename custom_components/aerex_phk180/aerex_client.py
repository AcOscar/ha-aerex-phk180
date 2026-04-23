"""HTTP-Client für die Aerex PHK180 Steuerung."""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from typing import Any

import aiohttp
from xml.etree import ElementTree

_LOGGER = logging.getLogger(__name__)

# Endpunkte
ENDPOINT_INDEX    = "index.cgx"
ENDPOINT_DETAILS  = "details.cgx"
ENDPOINT_SETTINGS = "settings.cgx"

# Betriebsarten (aus Betriebsart.html reverse-engineered)
BETRIEBSARTEN = {
    0: "Aus",
    1: "Warmwasser",
    2: "Manuell",
    3: "Auto Zeit",
    4: "Auto Sensor",
    6: "Unfall",
}

# Lüftungsstufen
LUFTSTUFEN = {
    0: "Aus",
    1: "Feuchteschutz",
    2: "Reduziert",
    3: "Nenn",
    4: "Intensiv",
}

# Schreib-Kommandos (aus HTML-Formularen reverse-engineered)
# C[register][kanal][richtung] = Wert ändern (0=erhöhen, 1=verringern)
# S[register][kanal]           = Wert setzen / umschalten
CMD_RAUMSOLL_UP   = "C[550][0][0]"   # +0.5°C
CMD_RAUMSOLL_DOWN = "C[550][0][1]"   # -0.5°C
CMD_ABSENKTEMP_UP   = "C[547][0][0]" # +0.5°C
CMD_ABSENKTEMP_DOWN = "C[547][0][1]" # -0.5°C
CMD_STOSSLÜFTUNG  = "S[229][0]"      # umschalten (0/1)
CMD_JAHRESZEIT    = "S[523][0]"      # umschalten (0=Winter, 1=Sommer)
CMD_FEHLER_RESET  = "S[313][0]"      # Fehler quittieren
CMD_FILTER0_RESET = "S[241][0]"      # Gerätefilter quittieren
CMD_FILTER1_RESET = "S[241][1]"      # Außenfilter quittieren


def _parse_float(value: str) -> float | None:
    """Extrahiert float-Wert aus Strings wie '20.5 °C', '2435 rpm', etc."""
    if not value or value.strip() in ("-", "- °C", "- ppm"):
        return None
    match = re.search(r"[-+]?\d+\.?\d*", value)
    return float(match.group()) if match else None


def _parse_int(value: str) -> int | None:
    """Extrahiert int-Wert aus String."""
    if not value or value.strip() == "-":
        return None
    match = re.search(r"[-+]?\d+", value)
    return int(match.group()) if match else None


def _parse_xml(xml_text: str) -> dict[str, str]:
    """Parst das CGX-XML-Format in ein einfaches Dict."""
    result: dict[str, str] = {}
    try:
        root = ElementTree.fromstring(xml_text)
        for text_elem in root.findall("text"):
            id_elem    = text_elem.find("id")
            value_elem = text_elem.find("value")
            if id_elem is not None and id_elem.text:
                result[id_elem.text] = (value_elem.text or "") if value_elem is not None else ""
    except ElementTree.ParseError as e:
        _LOGGER.error("XML-Parsing fehlgeschlagen: %s", e)
    return result


@dataclass
class AerexData:
    """Alle ausgelesenen Datenpunkte der PHK180."""

    # --- Index (Grundanzeige) ---
    betriebsmode: int | None = None
    betriebsartstring: str = "-"
    fan_mode: str = "-"
    absenktemperatur: float | None = None
    temp_raum: float | None = None
    soll_temp_raum: float | None = None
    stosslüftung_aktiv: bool = False
    jahreszeit: int | None = None          # 0=Winter, 1=Sommer
    ferien_ende: str = "-"
    warningword: int = 0
    statusword: int = 0
    error_id: int = 0
    error_sub_id: int = 0
    filter_meldung_geraet: bool = False
    filter_meldung_aussen: bool = False

    # --- Details (Abfrage) ---
    temp_raum_ext: float | None = None
    t_aul_vor_ewt: float | None = None
    t_lufteintritt: float | None = None
    temp_zuluft: float | None = None
    t_abluft: float | None = None
    he_wws_te: float | None = None         # Warmwasserspeicher oben
    he_wws_tw: float | None = None         # Warmwasserspeicher unten
    t_verdampfer: float | None = None
    fan_state_zu: int | None = None
    fan_state_ab: int | None = None
    bypass_zustand: str = "-"
    heat_pump_aktiv: bool = False
    ehz_aktiv: bool = False                # Elektroheizstab
    drehzahl_zu: int | None = None         # rpm Zuluft
    drehzahl_ab: int | None = None         # rpm Abluft
    co2_sensor1: int | None = None         # ppm
    co2_sensor2: int | None = None         # ppm
    co2_sensor3: int | None = None         # ppm
    rh_aktuell: float | None = None        # % relative Feuchte
    volumenstrom: int | None = None        # m³/h
    filter_restlaufzeit_geraet: int | None = None   # Tage
    filter_restlaufzeit_aussen: int | None = None   # Tage
    betriebsstunden_wp: int | None = None
    betriebsstunden_luft: int | None = None
    sw_version_lt: str = "-"

    # --- Settings ---
    wws_t_soll: float | None = None        # Warmwassersoll °C
    raumsolltemperatur: float | None = None


class AerexPHK180Client:
    """Kommuniziert mit dem eingebauten Webserver der Aerex PHK180."""

    def __init__(self, host: str, session: aiohttp.ClientSession, username: str = "", password: str = "") -> None:
        self._host = host.rstrip("/")
        self._session = session
        self._base_url = f"http://{self._host}"
        self._auth = aiohttp.BasicAuth(username, password) if username else None

    async def _get_cgx(self, endpoint: str) -> dict[str, str]:
        """Ruft eine CGX-Datei ab und gibt das geparste Dict zurück."""
        url = f"{self._base_url}/{endpoint}"
        try:
            async with self._session.get(url, auth=self._auth, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
                # Gerät liefert ISO-8859-1
                raw = await resp.read()
                text = raw.decode("iso-8859-1")
                return _parse_xml(text)
        except aiohttp.ClientError as e:
            _LOGGER.error("Verbindungsfehler zu %s: %s", url, e)
            raise

    async def async_get_data(self) -> AerexData:
        """Liest alle drei CGX-Endpunkte und gibt ein AerexData-Objekt zurück."""
        idx  = await self._get_cgx(ENDPOINT_INDEX)
        det  = await self._get_cgx(ENDPOINT_DETAILS)
        sett = await self._get_cgx(ENDPOINT_SETTINGS)

        data = AerexData(
            # Index
            betriebsmode       = _parse_int(idx.get("Betriebsmode", "")),
            betriebsartstring  = idx.get("Betriebsartstring", "-"),
            fan_mode           = idx.get("FanMode", "-"),
            absenktemperatur   = _parse_float(idx.get("AbsenkTemperatur", "")),
            temp_raum          = _parse_float(idx.get("TempRaum", "")),
            soll_temp_raum     = _parse_float(idx.get("SollTempRaum", "")),
            stosslüftung_aktiv = idx.get("IL_Aktiv", "0") == "1",
            jahreszeit         = _parse_int(idx.get("Jahreszeit", "")),
            ferien_ende        = idx.get("FerienEnde", "-"),
            warningword        = _parse_int(idx.get("Warningword", "0")) or 0,
            statusword         = _parse_int(idx.get("Statusword", "0")) or 0,
            error_id           = _parse_int(idx.get("Error_Id1", "0")) or 0,
            error_sub_id       = _parse_int(idx.get("Error_SubId1", "0")) or 0,
            filter_meldung_geraet = idx.get("FilterMeldung0", "0") == "1",
            filter_meldung_aussen = idx.get("FilterMeldung1", "0") == "1",

            # Details
            temp_raum_ext      = _parse_float(det.get("TempRaumExt", "")),
            t_aul_vor_ewt      = _parse_float(det.get("T_AUL_vor_EWT", "")),
            t_lufteintritt     = _parse_float(det.get("T_Lufteintritt", "")),
            temp_zuluft        = _parse_float(det.get("TempZuluft", "")),
            t_abluft           = _parse_float(det.get("T_Abluft", "")),
            he_wws_te          = _parse_float(det.get("HE_WWS_TE", "")),
            he_wws_tw          = _parse_float(det.get("HE_WWS_TW", "")),
            t_verdampfer       = _parse_float(det.get("tVerdampfer1", "")),
            fan_state_zu       = _parse_int(det.get("Fan_State1", "")),
            fan_state_ab       = _parse_int(det.get("Fan_State2", "")),
            bypass_zustand     = det.get("BypassZustand", "-"),
            heat_pump_aktiv    = det.get("HeatPump", "0") == "1",
            ehz_aktiv          = det.get("EHZ", "0") == "1",
            drehzahl_zu        = _parse_int(det.get("DrehzahlZu", "")),
            drehzahl_ab        = _parse_int(det.get("DrehzahlAb", "")),
            co2_sensor1        = _parse_int(det.get("Co2_AktValue1", "")),
            co2_sensor2        = _parse_int(det.get("Co2_AktValue2", "")),
            co2_sensor3        = _parse_int(det.get("Co2_AktValue3", "")),
            rh_aktuell         = _parse_float(det.get("Rh_AktValue", "")),
            volumenstrom       = _parse_int(det.get("Volumenstrom", "")),
            filter_restlaufzeit_geraet = _parse_int(det.get("Fan_GeraeteFilterRestlaufzeit", "")),
            filter_restlaufzeit_aussen = _parse_int(det.get("Fan_AussenFilterRestlaufzeit", "")),
            betriebsstunden_wp   = _parse_int(det.get("BSTD_WP", "")),
            betriebsstunden_luft = _parse_int(det.get("BSTD_Luftgesamt", "")),
            sw_version_lt      = det.get("SwVersionLT", "-"),

            # Settings
            wws_t_soll         = _parse_float(sett.get("WWS_T_Soll", "")),
            raumsolltemperatur = _parse_float(sett.get("Raumsolltemperatur", "")),
        )
        return data

    async def async_send_command(self, param: str, value: str, page: str = "index.htm") -> bool:
        """Sendet ein Schreib-Kommando an das Gerät via HTTP GET."""
        url = f"{self._base_url}/{page}"
        try:
            async with self._session.get(
                url,
                params={param: value},
                auth=self._auth,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                _LOGGER.debug("Kommando gesendet: %s=%s → HTTP %s", param, value, resp.status)
                return True
        except aiohttp.ClientError as e:
            _LOGGER.error("Fehler beim Senden von %s=%s: %s", param, value, e)
            return False

    async def async_set_raumsolltemperatur(self, ziel: float, aktuell: float) -> bool:
        """Setzt die Raumsolltemperatur durch schrittweises +/- (je 0.5°C)."""
        diff = round(ziel - aktuell, 1)
        steps = int(abs(diff) / 0.5)
        if steps == 0:
            return True
        cmd  = CMD_RAUMSOLL_UP if diff > 0 else CMD_RAUMSOLL_DOWN
        ok = True
        for _ in range(steps):
            ok = ok and await self.async_send_command(cmd, "0.5")
        return ok

    async def async_toggle_stosslüftung(self, aktiv: bool) -> bool:
        return await self.async_send_command(CMD_STOSSLÜFTUNG, "1" if aktiv else "0")

    async def async_toggle_jahreszeit(self, sommer: bool) -> bool:
        return await self.async_send_command(CMD_JAHRESZEIT, "1" if sommer else "0")

    async def async_set_betriebsart(self, modus: int) -> bool:
        """Setzt die Betriebsart.
        
        Parameter P[522][0] aus Betriebsart.html reverse-engineered.
        0=Aus, 1=Warmwasser, 2=Manuell, 3=Auto Zeit, 4=Auto Sensor, 6=Unfall
        """
        if modus not in (0, 1, 2, 3, 4, 6):
            raise ValueError(f"Ungültige Betriebsart: {modus}. Erlaubt: 0,1,2,3,4,6")
        return await self.async_send_command("P[522][0]", str(modus))

    async def async_set_luftstufe(self, stufe: int) -> bool:
        """Setzt die Lüftungsstufe (0=Aus, 1=Feuchteschutz, 2=Reduziert, 3=Nenn, 4=Intensiv).
        
        Parameter P[225][0] aus Luftstufe.html reverse-engineered.
        """
        if not 0 <= stufe <= 4:
            raise ValueError(f"Ungültige Lüftungsstufe: {stufe}. Erlaubt: 0–4")
        return await self.async_send_command("P[225][0]", str(stufe))

    async def async_reset_fehler(self) -> bool:
        return await self.async_send_command(CMD_FEHLER_RESET, "1")

    async def async_test_connection(self) -> bool:
        """Testet ob das Gerät erreichbar ist."""
        try:
            await self._get_cgx(ENDPOINT_INDEX)
            return True
        except Exception:
            return False
