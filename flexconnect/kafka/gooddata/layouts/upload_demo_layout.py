# (C) 2024 GoodData Corporation
import os
import time
from pathlib import Path

import orjson
import requests

fixtures_dir = Path(os.environ.get("FIXTURES_DIR", Path(__file__).parent))
print(f"{fixtures_dir=}", flush=True)
host = os.environ.get("HOST", "http://localhost:3000")
token = os.environ.get("TOKEN", "YWRtaW46Ym9vdHN0cmFwOmFkbWluMTIz")
header_host = os.environ.get("HEADER_HOST", None)
content_type_jsonapi = "application/vnd.gooddata.api+json"
content_type_default = "application/json"
headers = {"Host": header_host}
api_version = "v1"


def rest_op(op, url_path, data=None, raise_ex=True):
    all_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        **headers,
    }
    url = f"{host}/{url_path}"
    kwargs = {
        "url": url,
        "headers": all_headers,
    }
    if data:
        kwargs["json"] = data

    op_fnc = getattr(requests, op)
    response = op_fnc(**kwargs)

    if response.status_code < 200 or response.status_code > 299:
        if raise_ex:
            raise Exception(f"Call to {url} failed - {str(response.json())}")
        else:
            return None

    if response.status_code == 200:
        return response.json()
    else:
        return None


def read_data_from_file(data_json_path):
    with open(data_json_path) as f:
        return orjson.loads(f.read())


def rest_op_jsonapi(op, url_path, data_json_path=None, raise_ex=True):
    headers["Content-Type"] = content_type_jsonapi
    return rest_op(op, url_path, data_json_path, raise_ex)


def rest_op_default(op, url_path, data_json_path=None, raise_ex=True):
    headers["Content-Type"] = content_type_default
    return rest_op(op, url_path, data_json_path, raise_ex)


def wait_platform_up():
    # wait till GD.CN is up and ready to receive requests
    print("Waiting till AIO GD.CN is up", flush=True)
    while True:
        try:
            result = rest_op_jsonapi(
                "get",
                f"api/{api_version}/entities/admin/organizations/default",
                raise_ex=False,
            )
            if result is not None:
                print("AIO GD.CN is up", flush=True)
                break
            print("AIO GD.CN metadata does not responding", flush=True)
        except requests.exceptions.ConnectionError:
            print("AIO GD.CN is not available", flush=True)
        time.sleep(4)


def create_entity(entity_id, entity_data, entity_type, api_path, action):
    print(f"Creating {entity_type} id={entity_id}", flush=True)
    result = action("get", f"{api_path}/{entity_id}", raise_ex=False)
    if not result:
        return action("post", f"{api_path}", entity_data)
    else:
        print(f"Entity {entity_type} already exists id={entity_id} result={result}")
        return result


def update_layout():
    data_sources = read_data_from_file(fixtures_dir / "dataSources.json")
    hierarchy = read_data_from_file(fixtures_dir / "workspaces.json")

    wait_platform_up()

    print("Uploading test DS with physical model for demo", flush=True)
    rest_op_default("put", f"api/{api_version}/layout/dataSources", data_sources)

    print("Uploading workspaces", flush=True)
    rest_op_default("put", f"api/{api_version}/layout/workspaces", hierarchy)

    print("Layout configuration done successfully!", flush=True)


if __name__ == "__main__":
    update_layout()
