from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response

## AQUI
from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
import cbor
from hashlib import sha512
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionList
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.batch_pb2 import Batch
from sawtooth_sdk.protobuf.batch_pb2 import BatchList
import urllib.request
from urllib.error import HTTPError

context = create_context('secp256k1')
private_key = context.new_random_private_key()
signer = CryptoFactory(context).new_signer(private_key)
KEY_NAME = 'transfer-chain.keys'
API_URL = 'http://localhost:8000/api'

FAMILY = 'transfer-chain'
VERSION = '0.0'
PREFIX = '19d832'
## HASTA AQUI


# Create your views here.
class ProductViewSet(viewsets.ViewSet):
  # Required for the Browsable API renderer to have a nice form.
  #serializer_class = serializers.ProductSerializer

  # GET /products/
  def list(self, request):
    #serializer = serializers.TaskSerializer(
    #    instance=tasks.values(), many=True)

    response={
      "saludo":"hola"
    }

    return Response(response)
  
  # POST /products/
  def create(self, resquest):
    # encoding payload

    payload_bytes = cbor.dumps(resquest.data)
    
    print(resquest.data)
    print(payload_bytes)


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

    return Response(response)

  # GET /products/:id/
  def retrieve(self, request,pk=None):
    response = dict()

    response["id"] = pk
    response["data"] = request.data
    response["GET"] = request.GET
    response["POST"] = request.POST

    return Response(response)

  # PUT /products/:id/
  def update(self, request, pk=None):
    response = dict()

    response["id"] = pk
    response["data"] = request.data
    response["GET"] = request.GET
    response["POST"] = request.POST

    return Response(response)

  # DESTROY /products/:id/
  def destroy(self, request, pk=None):
    response = dict()

    response["id"] = pk
    response["HEY"] = "HEY!"
    response["data"] = request.data
    response["GET"] = request.GET
    response["POST"] = request.POST

    return Response(response)

  