from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests


class VerificarStatusPedido(Tool):
    def run(self, context: Context) -> TextResponse:
        self.weni_api_key = context.credentials.get("WENI_API_KEY")
        self.tray_url = context.credentials.get("TRAY_URL")
        self.weni_api_base_url = context.credentials.get("WENI_API_BASE_URL")
        self.id_do_pedido = context.parameters.get("id_do_pedido", "")

        result = self.tray_order_verifier()
        return TextResponse(text=str(result))


    def get_credentials_in_weni(self):
        url = f"{self.weni_api_base_url}/globals.json"
        headers = {
            "Content-type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.weni_api_key}",
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Error getting credentials from Weni: {e}")
            return None, None
        
        access_token = None
        refresh_token = None
        
        if "results" in data:
            for item in data["results"]:
                if item.get("key") == "access_token":
                    access_token = item.get("value")
                elif item.get("key") == "refresh_token":
                    refresh_token = item.get("value")
        
        if not access_token and len(data.get("results", [])) > 0:
             access_token = data["results"][0].get("value")
        if not refresh_token and len(data.get("results", [])) > 1:
             refresh_token = data["results"][1].get("value")
             
        return access_token, refresh_token

    def update_credentials_in_weni(self, access_token, refresh_token):
        headers = {
            "Content-type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.weni_api_key}",
        }

        try:
            if access_token:
                requests.post(
                    f"{self.weni_api_base_url}/globals.json?key=access_token", 
                    headers=headers,
                    json={"value": access_token}
                )
            if refresh_token:
                requests.post(
                    f"{self.weni_api_base_url}/globals.json?key=refresh_token", 
                    headers=headers,
                    json={"value": refresh_token}
                )
        except Exception as e:
            print(f"Error in update_credentials(): {e}")

        return {"message": "Credentials updated successfully"}

    def tray_refresh_auth(self, refresh_token):
        url = f"{self.tray_url}/web_api/auth?refresh_token={refresh_token}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")

            return access_token, refresh_token
        except Exception as e:
            print(f"Error in tray_refresh_auth(): {e}")
            return None, None


    def tray_order_verifier(self, retry=True):
        access_token, refresh_token = self.get_credentials_in_weni()
        
        if not access_token:
            return {"error": "Could not retrieve access token from Weni"}

        url = f"{self.tray_url}/web_api/orders/{self.id_do_pedido}?access_token={access_token}"
        
        try:
            response = requests.get(url)
            
            if response.status_code == 401:
                if retry:
                    print("Token expired, refreshing...")
                    new_access_token, new_refresh_token = self.tray_refresh_auth(refresh_token)
                    
                    if new_access_token and new_refresh_token:
                        self.update_credentials_in_weni(new_access_token, new_refresh_token)
                        return self.tray_order_verifier(retry=False)
                    else:
                        return {"error": "Failed to refresh token"}
                else:
                    return {"error": "Unauthorized after retry"}
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            return {"error": f"Error verifying order: {str(e)}"}