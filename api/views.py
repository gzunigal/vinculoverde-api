from django.shortcuts import render
from django.contrib.auth.models import AnonymousUser
from rest_framework import viewsets, exceptions, permissions
from rest_framework.response import Response

## AQUI
from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
import cbor
import json
from hashlib import sha512
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader, Transaction, TransactionList
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader, Batch, BatchList
import urllib.request
from urllib.error import HTTPError
import requests
import base64

context = create_context('secp256k1')
private_key = context.new_random_private_key()
signer = CryptoFactory(context).new_signer(private_key)
KEY_NAME = 'transfer-chain.keys'
API_URL = 'http://localhost:8000/api'

FAMILY = 'transfer-chain'
VERSION = '0.0'
PREFIX = '19d832'
## HASTA AQUI

class ProductViewSet(viewsets.ViewSet):
  # Required for the Browsable API renderer to have a nice form.
  #serializer_class = serializers.ProductSerializer

  # GET /products/
  def list(self, request):

    r = requests.get(API_URL+'/state',params={'address':PREFIX}).json()
    response = []
    for product in r['data']:
      decoded = base64.decodebytes(product['data'].encode())
      data = json.loads(decoded.decode())
      response.append(data)

    return Response(response)
  
  # POST /products/
  def create(self, request):
    print(request.data)
    # encoding payload
    payload = {
      "action":"create",
      "residuo":request.data
    }

    payload_bytes = cbor.dumps(payload)

    ## BUILD TRANSACTION
    # Build transaction header
    txn_header_bytes = TransactionHeader(
      family_name=FAMILY,
      family_version=VERSION,
      inputs=[PREFIX],
      outputs=[PREFIX],
      signer_public_key=signer.get_public_key().as_hex(),
      # In this example, we're signing the batch with the same private key,
      # but the batch can be signed by another party, in which case, the
      # public key will need to be associated with that key.
      batcher_public_key=signer.get_public_key().as_hex(),
      dependencies=[],
      payload_sha512=sha512(payload_bytes).hexdigest()
    ).SerializeToString()

    # Create transaction
    signature = signer.sign(txn_header_bytes)

    txn = Transaction(
      header=txn_header_bytes,
      header_signature=signature,
      payload= payload_bytes
    )

    # Encode the Transaction
    txn_list_bytes = TransactionList(
      transactions=[txn]
    ).SerializeToString()

    txn_bytes = txn.SerializeToString()

    ## BUILD BATCH
    # create batch header
    txns = [txn]

    batch_header_bytes = BatchHeader(
      signer_public_key=signer.get_public_key().as_hex(),
      transaction_ids=[txn.header_signature for txn in txns],
    ).SerializeToString()

    # create Batch
    signature = signer.sign(batch_header_bytes)

    batch = Batch(
      header=batch_header_bytes,
      header_signature=signature,
      transactions=txns
    )

    # BATCHLIST
    batch_list_bytes = BatchList(batches=[batch]).SerializeToString()

    response = None
    # ENVIAR A SERVIDOR 
    try:
      request = urllib.request.Request(
        API_URL+'/batches', ## URL SERVIDOR
        batch_list_bytes,
        method='POST',
        headers={'Content-Type': 'application/octet-stream'})
      response = urllib.request.urlopen(request)

    except HTTPError as e:
      response = e.file
    
    response = json.loads(response.read().decode('utf-8'))
    link = response["link"].split('=')[1]
    requests.get(API_URL+'/batch_statuses',params={'id':link, 'wait':1}).json()

    return self.retrieve(None,payload['residuo']['code'])

  # GET /products/:id/
  def retrieve(self, request,pk=None):
    r = requests.get(API_URL+'/state',params={'address':PREFIX}).json()
    for product in r['data']:
      decoded = base64.decodebytes(product['data'].encode())
      data = json.loads(decoded.decode())
      #data['bc_address'] = product['address']
      if data['code'] == pk:
        return Response(data)

    return Response('No existe producto')

  # PUT /products/:id/
  def update(self, request, pk=None):
    r = requests.get(API_URL+'/state',params={'address':PREFIX}).json()
    residuo = None
    for product in r['data']:
      decoded = base64.decodebytes(product['data'].encode())
      data = json.loads(decoded.decode())
      data['bc_address'] = product['address']
      if data['code'] == pk:
        residuo=data
        break

    if residuo == None:
      return Response('No existe producto')
    

    residuo['estados'].append(request.data)
    # encoding payload

    payload = {
      "action":"update",
      "residuo":residuo
    }

    payload_bytes = cbor.dumps(payload)

    ## BUILD TRANSACTION
    # Build transaction header
    txn_header_bytes = TransactionHeader(
      family_name=FAMILY,
      family_version=VERSION,
      inputs=[PREFIX],
      outputs=[PREFIX],
      signer_public_key=signer.get_public_key().as_hex(),
      # In this example, we're signing the batch with the same private key,
      # but the batch can be signed by another party, in which case, the
      # public key will need to be associated with that key.
      batcher_public_key=signer.get_public_key().as_hex(),
      dependencies=[],
      payload_sha512=sha512(payload_bytes).hexdigest()
    ).SerializeToString()

    # Create transaction
    signature = signer.sign(txn_header_bytes)

    txn = Transaction(
      header=txn_header_bytes,
      header_signature=signature,
      payload= payload_bytes
    )

    # Encode the Transaction
    txn_list_bytes = TransactionList(
      transactions=[txn]
    ).SerializeToString()

    txn_bytes = txn.SerializeToString()

    ## BUILD BATCH
    # create batch header
    txns = [txn]

    batch_header_bytes = BatchHeader(
      signer_public_key=signer.get_public_key().as_hex(),
      transaction_ids=[txn.header_signature for txn in txns],
    ).SerializeToString()

    # create Batch
    signature = signer.sign(batch_header_bytes)

    batch = Batch(
      header=batch_header_bytes,
      header_signature=signature,
      transactions=txns
    )

    # BATCHLIST
    batch_list_bytes = BatchList(batches=[batch]).SerializeToString()

    response = None
    # ENVIAR A SERVIDOR 
    try:
      request = urllib.request.Request(
        API_URL+'/batches', ## URL SERVIDOR
        batch_list_bytes,
        method='POST',
        headers={'Content-Type': 'application/octet-stream'})
      response = urllib.request.urlopen(request)

    except HTTPError as e:
      response = e.file

    response = json.loads(response.read().decode('utf-8'))
    link = response["link"].split('=')[1]
    requests.get(API_URL+'/batch_statuses',params={'id':link, 'wait':1}).json()

    return self.retrieve(None,pk)

  # DESTROY /products/:id/
  def destroy(self, request, pk=None):
    r = requests.get(API_URL+'/state',params={'address':PREFIX}).json()
    residuo = None
    for product in r['data']:
      decoded = base64.decodebytes(product['data'].encode())
      data = json.loads(decoded.decode())
      data['bc_address'] = product['address']
      if data['code'] == pk:
        residuo=data
        break

    if residuo == None:
      return Response('No existe producto')
    

    residuo['final']=True
    residuo['raws']=request.data
    # encoding payload

    payload = {
      "action":"finalice",
      "residuo":residuo
    }

    payload_bytes = cbor.dumps(payload)

    ## BUILD TRANSACTION
    # Build transaction header
    txn_header_bytes = TransactionHeader(
      family_name=FAMILY,
      family_version=VERSION,
      inputs=[PREFIX],
      outputs=[PREFIX],
      signer_public_key=signer.get_public_key().as_hex(),
      # In this example, we're signing the batch with the same private key,
      # but the batch can be signed by another party, in which case, the
      # public key will need to be associated with that key.
      batcher_public_key=signer.get_public_key().as_hex(),
      dependencies=[],
      payload_sha512=sha512(payload_bytes).hexdigest()
    ).SerializeToString()

    # Create transaction
    signature = signer.sign(txn_header_bytes)

    txn = Transaction(
      header=txn_header_bytes,
      header_signature=signature,
      payload= payload_bytes
    )

    # Encode the Transaction
    txn_list_bytes = TransactionList(
      transactions=[txn]
    ).SerializeToString()

    txn_bytes = txn.SerializeToString()

    ## BUILD BATCH
    # create batch header
    txns = [txn]

    batch_header_bytes = BatchHeader(
      signer_public_key=signer.get_public_key().as_hex(),
      transaction_ids=[txn.header_signature for txn in txns],
    ).SerializeToString()

    # create Batch
    signature = signer.sign(batch_header_bytes)

    batch = Batch(
      header=batch_header_bytes,
      header_signature=signature,
      transactions=txns
    )

    # BATCHLIST
    batch_list_bytes = BatchList(batches=[batch]).SerializeToString()


    response = None
    # ENVIAR A SERVIDOR 
    try:
      request = urllib.request.Request(
        API_URL+'/batches', ## URL SERVIDOR
        batch_list_bytes,
        method='POST',
        headers={'Content-Type': 'application/octet-stream'})
      response = urllib.request.urlopen(request)

    except HTTPError as e:
      response = e.file

    response = json.loads(response.read().decode('utf-8'))
    link = response["link"].split('=')[1]
    requests.get(API_URL+'/batch_statuses',params={'id':link, 'wait':1}).json()

    return self.retrieve(None,pk)

  