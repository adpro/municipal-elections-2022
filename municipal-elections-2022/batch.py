import requests
import argparse
from xml.etree import ElementTree


# namespaces
ns = {'base': 'http://www.volby.cz/kv/',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}


def download_batch(id: int):
    if id == 0:
        id = ""

    # SOAP request URL
    # url = "https://volby.cz/pls/kv2018/vysledky_okrsky?datumvoleb=20181005&davka=" + str(id)
    url = "https://www.volby.cz/pls/kv2022/vysledky_okrsky?davka=" + str(id)

    # headers
    headers = {
        'Content-Type': 'text/xml; charset=utf-8'
    }

    # POST request
    response = requests.request("GET", url, headers=headers)
    return response.text


def contains_org(org_id, xml):
    pos = xml.find('KODZASTUP="'+org_id+'"')
    if pos > -1: 
        print("Found")
        return True 
    else: 
        return False

if __name__ == "__main__":
    org_id = '562394' # CK
    org_batches = []
    batch_min = 1

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', "--min", help = "minimal batch id", type=int, default=1)
    args = parser.parse_args()
    if args.min:
        batch_min = args.min
    else:
        print(f"Minimal batch number: {args.min} has wrong format. Using default one..")

    try:
        xml_response = download_batch(0)
        root = ElementTree.fromstring(xml_response)
        el = root.find('.//base:DAVKA', ns)
        batch_max = 0
        if el is not None:
            batch_max = int(el.attrib['PORADI_DAVKY'])
        if batch_min > batch_max:
            batch_min = 1
        for i in range(batch_min, batch_max+1):
            print(f"Downloading batch id={i}...")
            xml = download_batch(i)
            if contains_org(org_id, xml):
                org_batches.append(xml)
        print(f"Amount of batches with org_id: {len(org_batches)}.")
    except requests.exceptions.ConnectionError as e:
        print("Error in downloading data!")
        print(f"Type of error: {type(e).__name__}")
        print(f"Reason: {e.args}")
    except Exception as e:
        print("Error in processing data!")
        print(f"Type of error: {type(e).__name__}")
        print(f"Reason: {e}")
    except KeyboardInterrupt:
        print("\nProgram aborted! Exiting...")