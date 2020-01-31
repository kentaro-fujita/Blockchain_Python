import sys
import json
import random
import pickle
from datetime import datetime
from hashlib import sha256

from argparse import ArgumentParser

from network import P2PNetwork

class Block(object):
  def __init__(self):
    self.index = 0
    self.prev_block = "0"*64
    self.difficulty = 5
    self.time = int(datetime.now().timestamp())
    self.tx = 'genesis'
    self.nonce = 0

  def json(self):
    json_data = {
      "index": self.index,
      "prev_block": self.prev_block,
      "time": self.time,
      "difficulty": self.difficulty,
      "tx": self.tx,
      "nonce": self.nonce,
    }
    return json_data
  
  def text(self):
    json_data = {
      "index": self.index,
      "prev_block": self.prev_block,
      "time": self.time,
      "difficulty": self.difficulty,
      "tx": self.tx,
      "nonce": self.nonce
    }
    return json.dumps(json_data, sort_keys=True, separators=(',', ':'))
  
  def load_from_json(self, block_json):
    self.index = block_json["index"]
    self.prev_block = block_json["prev_block"]
    self.time = block_json["time"]
    self.difficulty =block_json["difficulty"]
    self.tx = block_json["tx"]
    self.nonce = block_json["nonce"]

class Tool(object):
  def sha256_2(self, text):
    return sha256(sha256(text.encode('utf-8')).hexdigest().encode('utf-8')).hexdigest()

  def json2text(self, json_):
    return json.dumps(json_, sort_keys=True, separators=(',', ':'))
  
  def text2json(self, text):
    return json.loads(text)

class Blockchain(object):
  def __init__(self, offline, node_num, txs):
    self.block = Block()
    self.blockchain = [str(i) for i in range(100)]
    self.network = P2PNetwork(offline, node_num)

    self.tool = Tool()
    self.tx_pool = txs
    self.storage_txs = 3
    self.save_path = './block'+str(node_num)+'.txt'
    
    # start mining
    self.mining()

  def send_block(self, index, send_all=False):
    if send_all:
      for index in range(self.block.index):
        send_text = 'block '+self.blockchain[index]
        self.network.sender.send_msg(send_text)
    else:
      send_text = 'block '+self.blockchain[index]
      self.network.sender.send_msg(send_text)

  def recieve_inv(self, inv_msg):
    getdata_msg = 'getdata '+str(inv_msg)
    self.network.sender.send_msg(getdata_msg)

    for index in range(self.block.index):
      if self.blockchain[index] == str(index):
        getdata_msg = 'getdata '+str(index)
        self.network.sender.send_msg(getdata_msg)

  def find_nonce(self):
    while True:
      self.block.nonce = random.randint(0,2**30-1)
      hash_ = self.tool.sha256_2(self.block.text())
      difficulty = self.block.difficulty
      # print("\r"+hash_, end="")
      if len(self.network.receiver.msgs) != 0:
        return False
      else:
        if hash_[:difficulty].count('0') == difficulty:
          return True

  def mining(self):
    self.network.sender.send_msg('participate 0')

    # Proof of Works
    while True:
      # set transaction
      # txs = []
      # for j in range(self.storage_txs):
      #   index = random.randint(0, len(self.tx_pool)-1)
      #   tx = self.tx_pool[index]
      #   txs.append(tx)
      #   self.tx_pool.remove(tx)
      # tx = ','.join(txs)

      # find nance
      if self.find_nonce():
        inv_msg = 'inv '+str(self.block.index)
        self.network.sender.send_msg(inv_msg)
        self.blockchain[self.block.index] = self.block.text()
        self.block.prev_block = self.tool.sha256_2(self.block.text())
        self.block.index += 1
        self.block.time = int(datetime.now().timestamp())
        self.block.tx = 'transaction'
      # recive block
      else:
        for recieve_msg in self.network.receiver.msgs:
          flag, msg = recieve_msg.split(' ')
          if flag == 'participate':
            self.send_block(int(msg), send_all=True)
          elif flag == 'inv':
            self.recieve_inv(int(msg))
          elif flag == 'getdata':
            self.send_block(int(msg))
          elif flag == 'block':
            if self.validate_block(msg):
              self.block.prev_block = self.tool.sha256_2(msg)
              self.block.index += 1
              self.block.time = int(datetime.now().timestamp())
              self.block.tx = 'transaction'
          self.network.receiver.msgs.remove(recieve_msg)
      self.save()

    return self.find_nonce(tx)
  
  def validate_block(self, block_text):
    block_json = self.tool.text2json(block_text)
    block_hash = self.tool.sha256_2(block_text)

    difficulty = self.block.difficulty
    if block_hash[:block_json['difficulty']].count('0') == difficulty:
      index = block_json['index']
      if self.block.index < index:
        self.block.load_from_json(block_json)
        self.blockchain[index] = block_text
        return True
      elif index == 0:
        print("Genesis Block")
        self.block.load_from_json(block_json)
        self.blockchain[index] = block_text
        return False
      elif block_json["prev_block"] == self.tool.sha256_2(self.blockchain[index-1]):
        self.blockchain[index] = block_text
    else:
      print("Invalid Block")
      return False
  
  def add_tx(self, tx):
    self.tx_pool.append(tx)

  def save(self):
    with open(self.save_path, 'w') as f:
      for data in self.blockchain:
        f.write(data+'\n')

def parser():
  usage = 'Usage: python {} [-o] [-n]'.format(__file__)

  parser = ArgumentParser(usage=usage)
  parser.add_argument('--offline', '-o',help='オフラインフラグ',action='store_true')
  parser.add_argument('--num', '-n', help='ノード番号')

  args = parser.parse_args()

  return args.offline, args.num

def main():
  offline, node_num = parser()
  txs = ["A→B $100", "B→C $50", "B→A $40", "C→A $30", "A→D $200", "E→B $50", \
      "F→D $60", "C→A $100", "E→A $70", "G→C $40", "C→A $90", "A→F $150"]
  
  tx = 'transactions'
  blockchain = Blockchain(offline, node_num, txs)

if __name__ == '__main__':
  main()