from pysnmp.carrier.asynsock.dgram import udp
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import cmdrsp, context
from pysnmp.proto.api import v2c

class SNMP_Server:
    def __init__(self, listen_ip, listen_port):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.snmp_engine = engine.SnmpEngine()

    def start(self):
        # SNMP sunucusunu başlatma ve dinlemeye başlama
        config.addTransport(
            self.snmp_engine,
            udp.domainName + (1,),
            udp.UdpTransport().openServerMode((self.listen_ip, self.listen_port))
        )
        config.addSocketTransport(
            self.snmp_engine,
            udp.domainName + (2,),
            udp.Udp6Transport().openServerMode((self.listen_ip, self.listen_port))
        )
        cmdrsp.GetCommandResponder(self.snmp_engine, self.process_snmp_request)
        cmdrsp.NextCommandResponder(self.snmp_engine, self.process_snmp_request)
        self.snmp_engine.transportDispatcher.jobStarted(1)
        self.snmp_engine.transportDispatcher.runDispatcher()

    def process_snmp_request(self, snmp_engine, state_reference, context_name, var_binds, cb_ctx):
        # SNMP isteğini işleme ve yanıt gönderme
        pdu_version = snmp_engine.msgAndPduDsp.getPDU(state_reference).getComponentByPosition(1).getComponentByPosition(0).getComponentByPosition(0).getComponent()
        if pdu_version == v2c.apiVersion:
            error_status = v2c.apiPDU.getVarBinds(state_reference).get(0).get('statusInformation')
            if error_status:
                print(f"SNMP Hatası: {error_status.prettyPrint()}")
                return
        else:
            print(f"Desteklenmeyen SNMP sürümü: {pdu_version}")
            return

        # Yanıt olarak gönderilecek verileri hazırlama
        var_binds = v2c.apiPDU.getVarBinds(state_reference)
        response_var_binds = []

        for oid, value in var_binds:
            # İstenen OID'lere bağlı olarak yanıt verilerini oluşturma
            if oid == '1.3.6.1.2.1.1.1.0':
                response_var_binds.append((oid, 'System Description'))
            elif oid == '1.3.6.1.2.1.1.2.0':
                response_var_binds.append((oid, 'System Object ID'))
            # Diğer OID'lere göre devam eder...

        # Yanıtı gönderme
        snmp_engine.msgAndPduDsp.returnResponse(state_reference, response_var_binds)




    def stop(self):
    # SNMP sunucusunu durdurma
        self.snmp_engine.transportDispatcher.jobFinished(1)
        self.snmp_engine.transportDispatcher.closeDispatcher()



# Örnek kullanım
if __name__ == '__main__':
    server = SNMP_Server(listen_ip='0.0.0.0', listen_port=161)
    server.start()
