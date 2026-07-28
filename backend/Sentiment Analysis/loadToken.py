from dotenv import load_dotenv
import os

load_dotenv()
_polygon_token = os.environ.get('POLYGON_TOKEN')

def load_token():
    return _polygon_token
