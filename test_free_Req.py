from FreeReq import ReqModel
from FreeReq import ReqSingleJsonFileAgent
from pytestqt.modeltest import ModelTester


def est_model(self):
    req_agent = ReqSingleJsonFileAgent()
    req_agent.init()
    if not req_agent.open_req('FreeReq'):
        req_agent.new_req('FreeReq', True)

    req_model = ReqModel(req_agent)

    qtmodeltester = ModelTester()
    qtmodeltester.check(req_model)

