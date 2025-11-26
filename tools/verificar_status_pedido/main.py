from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests


class VerificarStatusPedido(Tool):
    def execute(self, context: Context) -> TextResponse:
        cep = context.parameters.get("cep", "")
        print(cep)
        address_response = self.get_address_by_cep(cep=cep)
        print(address_response)
        return TextResponse(data=address_response)

    def get_address_by_cep(self, cep):
        url = f"https://viacep.com.br/ws/{cep}/json/"
        response = requests.get(url)
        return response.json()
