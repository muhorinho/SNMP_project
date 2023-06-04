import time
import csv

import requests
import json

from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch
from pysnmp.entity.rfc3413.oneliner import cmdgen

class SNMP_Client:
    def __init__(self, controller_ip):
        self.controller_ip = controller_ip
        self.csv_filename = "metrics.csv"
        self.metric_headers = ["Device", "Metric"]

    def get_metrics_and_save_to_csv(self, target_ip):
        while True:
            # SNMP isteği oluşturma ve metrikleri alıp CSV dosyasına kaydetme
            errorIndication, errorStatus, errorIndex, varBinds = cmdgen.CommandGenerator().nextCmd(
                cmdgen.CommunityData('public'),
                cmdgen.UdpTransportTarget((target_ip, 161)),
                cmdgen.MibVariable('HOST-RESOURCES-MIB', 'hrProcessorLoad'),
                cmdgen.MibVariable('IF-MIB', 'ifInOctets'),
                lookupNames=True,
                lookupValues=True
            )

            if errorIndication:
                print(f"SNMP Hatası: {errorIndication}")
            elif errorStatus:
                print(f"SNMP Hatası: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex)-1][0] or '?'}")
            else:
                # Metrikleri çıkarma ve CSV dosyasına kaydetme işlemleri
                metrics = self.extract_metrics(varBinds)
                self.save_metrics_to_csv(metrics)

            
            time.sleep(60)

    def extract_metrics(self, varBinds):
        
        metrics = []
        for varBind in varBinds:
            metric = f"{varBind[0][0]} = {varBind[1]}"
            metrics.append(metric)
        return metrics

    def save_metrics_to_csv(self, metrics):
        
        with open(self.csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            
            if file.tell() == 0:
                writer.writerow(self.metric_headers)

            # Her bir metriği CSV dosyasına yaz
            for metric in metrics:
                writer.writerow([self.controller_ip, metric])


def create_topology():
    net = Mininet(controller=Controller, switch=OVSSwitch)

    # Anahtarlayıcıları ekleme
    switch1 = net.addSwitch('s1', protocols='OpenFlow13')
    switch2 = net.addSwitch('s2', protocols='OpenFlow13')

    # Ana bilgisayarları ekleme
    host1 = net.addHost('h1', ip='10.0.0.1')
    host2 = net.addHost('h2', ip='10.0.0.2')

    # Bağlantıları tanımlama
    net.addLink(host1, switch1)
    net.addLink(switch1, switch2)
    net.addLink(switch2, host2)

    # Topolojiyi başlatma
    net.start()

    # Kontrolleri yapılandırma
    controller = net.controllers[0]
    controller_ip = controller.IP()

    # OpenDaylight Controller API'sini kullanarak anahtarlayıcıları yapılandırma
    configure_switches(controller_ip)

    # SNMP istemcisini başlatma
    snmp_client = SNMP_Client(controller_ip)
    snmp_client.get_metrics_and_save_to_csv(host1.IP())

    # Mininet'i durdurma
    net.stop()


def configure_switches(controller_ip):
    # OpenDaylight Controller'a POST isteği göndererek anahtarlayıcıları yapılandırma
    headers = {'Content-Type': 'application/json'}
    
    # Anahtarlayıcı 1 (s1) yapılandırması
    switch1_data = {
        "node": [
            {
                "id": "s1",
                "flow-node-inventory:table": [
                    {
                        "id": 0,
                        "flow": [
                            {
                                "id": "flow1",
                                "match": {
                                    "ethernet-match": {
                                        "ethernet-type": {
                                            "type": 2048
                                        }
                                    }
                                },
                                "instructions": {
                                    "instruction": [
                                        {
                                            "order": 0,
                                            "apply-actions": {
                                                "action": [
                                                    {
                                                        "order": 0,
                                                        "output-action": {
                                                            "output-node-connector": "2"
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    ]
                                },
                                "priority": 10
                            }
                        ]
                    }
                ]
            }
        ]
    }

    # Anahtarlayıcı 2 (s2) yapılandırması
    switch2_data = {
        "node": [
            {
                "id": "s2",
                "flow-node-inventory:table": [
                    {
                        "id": 0,
                        "flow": [
                            {
                                "id": "flow1",
                                "match": {
                                    "ethernet-match": {
                                        "ethernet-type": {
                                            "type": 2048
                                        }
                                    }
                                },
                                "instructions": {
                                    "instruction": [
                                        {
                                            "order": 0,
                                            "apply-actions": {
                                                "action": [
                                                    {
                                                        "order": 0,
                                                        "output-action": {
                                                            "output-node-connector": "2"
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    ]
                                },
                                "priority": 10
                            }
                        ]
                    }
                ]
            }
        ]
    }

    # Anahtarlayıcı 1 (s1) yapılandırmasını OpenDaylight Controller'a gönderme
    switch1_url = f"http://192.168.1.8:8181/restconf/config/opendaylight-inventory:nodes/node/s1"
    response1 = requests.put(switch1_url, headers=headers, data=json.dumps(switch1_data))

    # Anahtarlayıcı 2 (s2) yapılandırmasını OpenDaylight Controller'a gönderme
    switch2_url = f"http://192.168.1.8:8181/restconf/config/opendaylight-inventory:nodes/node/s2"
    response2 = requests.put(switch2_url, headers=headers, data=json.dumps(switch2_data))

    if response1.status_code == 200 and response2.status_code == 200:
        print("Anahtarlayıcı yapılandırması başarıyla tamamlandı.")
    else:
        print("Anahtarlayıcı yapılandırması başarısız oldu.")




# Topolojiyi oluşturma
if __name__ == '__main__':
    create_topology()
