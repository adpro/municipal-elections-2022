import requests
import argparse
import math
from xml.etree import ElementTree
from datetime import date, datetime 
from dataclasses import dataclass

##### CLASSES #####
@dataclass
class Municipality:
    timestamp: datetime = date.min
    code: str = ""
    name: str = ""
    councilor_amount: int = 0
    final: bool = False

@dataclass
class PoliticalParty:
    order: int = 0
    name: str = ""
    votes: int = 0
    candidates_amount: int = 0
    councilor_amount: int = 0
    councilor_amount_calc: int = 0

@dataclass
class Turnout:
    submitted_envelopes: int = 0
    valid_votes: int = 0
    polling_divisions: int = 0
    polling_divisions_processed: int = 0

##### GLOBAL #####

# namespaces
ns = {'base': 'http://www.volby.cz/kv/',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}


##### FUNCTIONS #####

# truncate float to N decimal positions
def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n

# download xml
def download_statement(org: str, previous: bool):

    # SOAP request URL
    if previous == False:
        url = "https://volby.cz/pls/kv2022/vysledky_obec?cislo_obce=" + org
    else:
        url = "https://volby.cz/pls/kv2018/vysledky_obec?datumvoleb=20181005&cislo_obce=" + org

    # headers
    headers = {
        'Content-Type': 'text/xml; charset=utf-8'
    }

    # POST request
    response = requests.request("GET", url, headers=headers)
    return response.text


def fill_municipality(root, data):
    data.timestamp = datetime.fromisoformat(root.attrib['DATUM_CAS_GENEROVANI'])
    el = root.find('.//base:OBEC', ns)
    if el is not None:
        data.code = el.attrib['KODZASTUP']
        data.name = el.attrib['NAZEVZAST']
        data.councilor_amount = int(el.attrib['VOLENO_ZASTUP'])
        data.final = False if el.attrib['JE_SPOCTENO'] == 'false' else True
    

def fill_turnout(root, data):
    el = root.find('.//base:OBEC/base:VYSLEDEK/base:UCAST', ns)
    if el is not None:
        data.submitted_envelopes = int(el.attrib['ODEVZDANE_OBALKY'])
        data.valid_votes = int(el.attrib['PLATNE_HLASY'])
        data.polling_divisions = int(el.attrib['OKRSKY_CELKEM'])
        data.polling_divisions_processed = int(el.attrib['OKRSKY_ZPRAC'])


def fill_political_parties(root):
    parties = []
    els = root.findall('.//base:OBEC/base:VYSLEDEK/base:VOLEBNI_STRANA', ns)
    for el in els:
        party = PoliticalParty()
        party.order = int(el.attrib['POR_STR_HLAS_LIST'])
        party.name = el.attrib['NAZEV_STRANY']
        party.votes = int(el.attrib['HLASY'])
        party.candidates_amount = int(el.attrib['KANDIDATU_POCET'])
        party.councilor_amount = int(el.attrib['ZASTUPITELE_POCET'])
        parties.append(party)
    return parties

## according to https://volby.cz/prg/SebranicePř%C3%ADkladZápisZO18.pdf
def calc_election_step_A(municipality, voted, parties):
    scrutiny = []   # list of parties to scrutiny step
    pct = 5
    while True:
        for party in parties:
            base = voted.valid_votes / municipality.councilor_amount * min(municipality.councilor_amount, party.candidates_amount)
            if party.votes > 0:
                ratio = party.votes / base * 100
            else:
                ratio = 0
            if ratio >= pct:
                scrutiny.append(party)
        if len(scrutiny) < 2:
            scrutiny = []
            pct -= 1
        else:
            return scrutiny
            # break

# scrutiny part of calculation
def calc_election_step_B(municipality, voted, parties):
    ratios = [] # list of tuples (party ratio, party code)
    for party in parties:
        for i in range(1, party.candidates_amount+1):
            ratios.append( (truncate(party.votes / i, 2), party.order) )
    return ratios


# sorting ratios
def calc_election_step_C(ratios, parties):
    ratios.sort(key=lambda x: x[0], reverse=True)
    return ratios

# distribution of mandates to parties
def calc_election_step_D(ratios, parties, municipality, voted):
    if voted.polling_divisions_processed == 0:
        return
    mandates_ratios = ratios[:municipality.councilor_amount]
    for party in parties:
        party.councilor_amount_calc = sum(1 for key,value in mandates_ratios if value == party.order)


def print_mandates_amount(parties):
    parties.sort(key=lambda x:x.councilor_amount_calc, reverse=True)
    print("Mandates   M.Off.   Party")
    print("--------   ------   -----")
    for party in parties:
        print(f"{party.councilor_amount_calc:>8}   {party.councilor_amount:>6}   {party.name}")


if __name__ == "__main__":

    # input variables
    org_id = '562394' # CK

    parser = argparse.ArgumentParser()
    parser.add_argument("--org", help = "set organization id", type=str)
    parser.add_argument('-p', "--previous", action='store_true', help="previous elections in 2018")
    
    args = parser.parse_args()
    if args.org:
        if  len(args.org) == 6:
            org_id = args.org
        else:
            print(f"Organization ID: {args.org} has wrong format. Using default one..")

    print(f"Using org id: {org_id}")

    print("Downloading xml from volby.cz ...")
    xml_response = download_statement(org_id, args.previous)
    root = ElementTree.fromstring(xml_response)
    data_municipality = Municipality()
    data_voted = Turnout()
    print("Parsing input xml data...")
    fill_municipality(root, data_municipality)
    fill_turnout(root, data_voted)
    data_parties = fill_political_parties(root)
    
    ## data are prepared, we can calculate election results
    print("Calculating election results...")
    scrutiny_parties = calc_election_step_A(data_municipality, data_voted, data_parties)
    votes_ratios = calc_election_step_B(data_municipality, data_voted, scrutiny_parties)
    ratios = calc_election_step_C(votes_ratios, scrutiny_parties)
    mandates = calc_election_step_D(ratios, scrutiny_parties, data_municipality, data_voted)
    
    ## we have calculated mandates, now show them
    str_final = " INCOMPLETE RESULTS"
    if data_municipality.final:
        str_final = " FINAL RESULTS"
    print(f"\nCalculated municipal elections results for {data_municipality.name}")
    print(f"Timestamp: {data_municipality.timestamp}, district parts {data_voted.polling_divisions_processed}/{data_voted.polling_divisions}{str_final}:")
    print("="*80)
    print_mandates_amount(data_parties)

    print("\n")