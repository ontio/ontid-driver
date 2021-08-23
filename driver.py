#!/usr/bin/env python3

from ontology.sdk import Ontology
from ontology.vm import build_vm
from ontology.core.transaction import Transaction
import re
from aiohttp import web
import logging


__version__ = "0.1.0"


async def get_ddo(ont_id):
    contract_address = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03'
    version = b'\x00'
    remote = 'http://dappnode1.ont.io:20336/'

    sdk = Ontology(rpc_address=remote)
    args = dict(ontid=ont_id.encode('utf-8'))
    invoke_code = build_vm.build_native_invoke_code(
        contract_address, version, 'getDocumentJson', args)
    tx = Transaction(0, 0xd1, 0, 0, b'', invoke_code)
    response = await sdk.aio_rpc.send_raw_transaction_pre_exec(tx)
    ddo = response['Result']

    return ddo

async def handle(request):
    id = request.match_info.get('id', '')
    if not re.match('^did:ont:(.*)$', id):
        return web.Response()

    ddo = await get_ddo(id)
    if ddo:
        res = bytes.fromhex(ddo).decode('utf-8')
    else:
        logging.info("cannot resolves %s", id)
        res = None
    # fix issue #1
    headers = {'Content-Type': 'application/did+ld+json'}
    return web.Response(text=res, headers=headers)


def run():
    app = web.Application()
    app.add_routes([
        web.get('/1.0/identifiers/{id}', handle)
    ])
    web.run_app(app)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info("Start ontid driver")
    run()
