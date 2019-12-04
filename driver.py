#!/usr/bin/env python3

from ontology.sdk import Ontology
from ontology.vm import build_vm
from ontology.core.transaction import Transaction
from ontology.contract.native import ontid
from ontology.crypto.curve import Curve
from ontology.io.memory_stream import StreamManager
from ontology.io.binary_reader import BinaryReader
from ontology.exception.exception import SDKException
from ontology.exception.error_code import ErrorCode
from ontology.common.address import Address
import re
import json
from aiohttp import web
import logging


async def get_ddo(ont_id):
    contract_address = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03'
    version = b'\x00'
    remote = 'http://dappnode1.ont.io:20336/'

    sdk = Ontology(rpc_address=remote)
    args = dict(ontid=ont_id.encode('utf-8'))
    invoke_code = build_vm.build_native_invoke_code(
        contract_address, version, 'getDDO', args)
    tx = Transaction(0, 0xd1, 0, 0, b'', invoke_code)
    response = await sdk.aio_rpc.send_raw_transaction_pre_exec(tx)
    serialized_ddo = response['Result']

    if len(serialized_ddo) == 0:
        return dict()
    if isinstance(serialized_ddo, str):
        stream = StreamManager.get_stream(bytearray.fromhex(serialized_ddo))
    elif isinstance(serialized_ddo, bytes):
        stream = StreamManager.get_stream(serialized_ddo)
    else:
        raise SDKException(ErrorCode.params_type_error(
            'unexpected data type {}'.format(type(serialized_ddo))))
    reader = BinaryReader(stream)
    try:
        public_key_bytes = reader.read_var_bytes()
    except SDKException:
        public_key_bytes = b''
    try:
        attribute_bytes = reader.read_var_bytes()
    except SDKException:
        attribute_bytes = b''
    try:
        recovery_bytes = reader.read_var_bytes()
    except SDKException:
        recovery_bytes = b''
    if len(recovery_bytes) != 0:
        b58_recovery = Address(recovery_bytes).b58encode()
    else:
        b58_recovery = ''
    try:
        controller = reader.read_var_bytes().decode('utf-8')
    except SDKException:
        controller = ''
    try:
        recovery = reader.read_var_bytes().decode('utf-8')
    except SDKException:
        recovery = ''

    pub_keys = ontid.OntId.parse_pub_keys(ont_id, public_key_bytes)
    attribute_list = ontid.OntId.parse_attributes(attribute_bytes)
    return dict(
        id=ont_id,
        keys=pub_keys,
        ctrl=controller,
        attributes=attribute_list,
        recovery=recovery if recovery else b58_recovery,
    )


def get_key_type(key):
    if key['Type'] == 'ECDSA':
        if key['Curve'] == Curve.P224.name:
            return 'EcdsaSecp224r1VerificationKey2019'
        elif key['Curve'] == Curve.P256.name:
            return 'EcdsaSecp256r1VerificationKey2019'
        elif key['Curve'] == Curve.P384.name:
            return 'EcdsaSecp384r1VerificationKey2019'
        elif key['Curve'] == Curve.P521.name:
            return 'EcdsaSecp521r1VerificationKey2019'
    elif key['Type'] == "EDDSA":
        return 'Ed25519VerificationKey2018'
    elif key['Type'] == 'SM2':
        return 'SM2VerificationKey2019'
    else:
        raise Exception('unknown verification key type {}'.format(key['Type']))


def make_did_document(ddo):
    doc = {
        '@context': 'https://w3id.org/did/v1',
        'id': ddo['id'],
        'authentication': [],
        'publicKey': [],
    }
    for k in ddo['keys']:
        doc['publicKey'].append(dict(
            id=k['PubKeyId'],
            type=get_key_type(k),
            controller=ddo['id'],
            publicKeyHex=k['Value'],
        ))
        doc['authentication'].append(k['PubKeyId'])
    if 'ctrl' in ddo:
        doc['controller'] = ddo['ctrl']
    if 'recovery' in ddo:
        doc['recovery'] = ddo['recovery']
    for a in ddo['attributes']:
        if a['Type'] == 'service':
            srvc = a['Value']
            srvc['id'] = ddo['id'] + '#' + a['Key']
            if 'service' not in doc:
                doc['service'] = []
            doc['service'].append(srvc)
        else:
            if 'attribute' not in doc:
                doc['attribute'] = []
                doc['attribute'].append(dict(
                    id=ddo['id'] + '#' + a['Key'],
                    type=a['Type'],
                    value=a['Value'],
                ))

    return json.dumps(doc, indent=2)


async def handle(request):
    id = request.match_info.get('id', '')
    if not re.match('^did:ont:(.*)$', id):
        return web.Response()

    ddo = await get_ddo(id)
    if ddo:
        res = make_did_document(ddo)
    else:
        logging.info("cannot resolves %s", id)
        res = None
    return web.Response(text=res)


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
