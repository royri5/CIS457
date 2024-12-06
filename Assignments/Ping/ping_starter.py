# Author: Richard Roy
from socket import gethostbyname, getprotobyname, socket, SOCK_RAW, AF_INET, htons, inet_ntoa
from os import getpid
import sys
from struct import pack, unpack_from
from time import time, sleep
from select import select
# Reference: https://docs.python.org/3/howto/argparse.html#argparse-tutorial
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("hostname", help="The hostname or IP address to ping", type=str)
parser.add_argument("-i", "--interval", help="Set the interval between sending packets to INTERVAL seconds", type=int)
parser.add_argument("-t", "--timeout", help="Set the timeout for waiting for a reply to TIMEOUT seconds", type=float)
parser.add_argument("-n", "--packets", help="Stop after sending PACKETS packets", type=int)
args = parser.parse_args()
import math

ICMP_ECHO_REQUEST = 8


def checksum(sdata):
  csum = 0
  
  # Pad with zero if we have odd number of bytes
  if len(sdata) % 2:
    data += b'\x00'
    
  for i in range(0, len(sdata), 2):
    # Take each 16-bit as an unsigned integer
    word = (sdata[i] << 8) + sdata[i+1]
    csum += word
  # Add back the carry value to the current sum
  csum = (csum >> 16) + (csum & 0xFFFF)
  # Just in case the above sum has carry bits
  csum = csum + (csum >> 16)
  
  # Return the lowest 16 bits of the 1s complement   
  return ~csum & 0xFFFF

def receiveOnePing(mySocket, ID, timeout, destAddr, expected_seq):
  timeLeft = timeout
  # holder vars for printing
  remote_ip = None
  icmp_seq = None
  ttl = None
  rtt = None

  while True:
    startedSelect = time()
    whatReady = select([mySocket], [], [], timeout)
    howLongInSelect = time()  - startedSelect
    # this checks if we got anything back yet, breaking if we did
    if whatReady[0] == []:
      timeLeft = timeLeft - howLongInSelect
      # this checks if we timed out
      if timeLeft <= 0:
        print(f"Request timeout for icmp_seq {expected_seq}")
        return None   # timeout
    else:
      timeReceived = time()
      # if it is not ours, we still have to keep going and waiting for timeout
      timeLeft = timeLeft - howLongInSelect

      recPacket,addr = mySocket.recvfrom(1024)

      ## Fetch the IP header fields
      # ip header contains just ttl, 8 bytes in, it is 1 byte long
      ip_header = unpack_from("b", recPacket, 8)
      #ttl = ttl[0] # untuple it
      
      ## Fetch the ICMP header fields
      # icmp_header contains the whole header, but we only care about the sequence number
      # and the pid
      icmp_header = unpack_from("bbHHH", recPacket, 20)
      
      # check if the packet is ours
      pid = icmp_header[3]
      if pid != ID:
        print(f"Foreign ICMP packet with PID {pid} received")
        continue

      break

  # confirmed it's ours, let's get the data
  remote_ip = addr[0]
  icmp_seq = icmp_header[4]
  ttl = ip_header[0]
  # payload is the time we sent the packet
  payload = unpack_from("d", recPacket, 28)
  # rtt in ms
  rtt = (timeReceived - payload[0]) * 1000

  print(f"Reply from {remote_ip}: icmp_seq={icmp_seq} ttl={ttl} time={rtt:.4f} ms")

  return rtt

def sendOnePing(mySocket, destAddr, ID, seq_num):
  
  # ICMP header fields: 
  #    type      (1 byte) 
  #    code      (1 byte)
  #    checksum  (2 bytes)
  #    id        (2 bytes)
  #    sequence  (2 bytes)
  
  # Make a dummy header with 0 checksum
  myChecksum = 0
  header = pack("bbHHH", ICMP_ECHO_REQUEST, 0, myChecksum, ID, seq_num)
  data = pack("d", time())
  # calculate the checksum on the header and dummy data
  myChecksum = checksum(header+data)
  header = pack("bbHHH", ICMP_ECHO_REQUEST, 0, htons(myChecksum), ID, seq_num)
  packet = header+data  
  mySocket.sendto(packet, (destAddr, 1))

def doOnePing(destAddr, timeout, seq_num):
  icmp = getprotobyname("icmp")
  mySocket = socket(AF_INET, SOCK_RAW, icmp)
  # Use the lowest 16-bit of the PID
  myID = getpid() & 0xFFFF
  sendOnePing(mySocket, destAddr, myID, seq_num)
  rtt = receiveOnePing(mySocket, myID, timeout, destAddr, seq_num)
  mySocket.close()
  return rtt

def ping(host, timeout): # TODO: 
  #holder vars for printing
  num_pkts_transmitted = 0
  num_pkts_received = 0
  min_rtt = None
  max_rtt = None
  avg_rtt = None
  rtt_arr = []
  seq_num = 0 

  # interval arg functionality
  interval = 1
  if args.interval:
    interval = args.interval

  # packet count arg functionality
  num_to_send = None
  if args.packets:
    num_to_send = args.packets

  try:
    dest = gethostbyname(host)
    print (f"PING {host} ({dest}) ")
    while True:

      # packet count arg functionality
      if num_to_send is not None:
        if num_pkts_transmitted == num_to_send:
          break

      rtt = doOnePing(dest, timeout, seq_num)
      seq_num += 1
      num_pkts_transmitted += 1
      # check if we have a new rtt to add to our stats (reply received)
      if rtt is not None:
        rtt_arr.append(rtt)
        num_pkts_received += 1
        if min_rtt is None or rtt < min_rtt:
          min_rtt = rtt
        if max_rtt is None or rtt > max_rtt:
          max_rtt = rtt
      sleep(interval)

  except Exception as e:
    print(f"Exception: {e}")
    return
  
  except KeyboardInterrupt:
    # still want stats even if we let it finish with -n option, so letting it fall through
    pass

  finally:
    # avoid division by zero/empty array
    if num_pkts_received == 0:
      avg_rtt = None
      if num_pkts_transmitted == 0:
        # no packets sent, stats are misleading so omitted, triggered due to host not found
        return
      # no packets received, so no rtt to calculate
      print(f"\n--- ping statistics ---")
      print(f"{num_pkts_transmitted} packets transmitted\n{num_pkts_received} packets received\nMinimum Round Trip Time: {min_rtt} ms\nMaximum Round Trip Time: {max_rtt} ms\nAverage Round Trip Time: {avg_rtt} ms")
    else:
      avg_rtt = math.fsum(rtt_arr) / num_pkts_received
      print(f"\n--- ping statistics ---")
      print(f"{num_pkts_transmitted} packets transmitted\n{num_pkts_received} packets received\nMinimum Round Trip Time: {min_rtt:.4f} ms\nMaximum Round Trip Time: {max_rtt:.4f} ms\nAverage Round Trip Time: {avg_rtt:.4f} ms")
    return
  
if __name__ == "__main__": # TODO:
  # holder vars
  # timeout arg functionality
  timeout = 1
  if args.timeout:
    timeout = args.timeout

  if len(sys.argv) < 2:
    print(f"Use {sys.argv[0]} hostname")
  else:
    # vvv test printing arguments for debugging/verifying cmd line args vvv
    #print(f"Interval: {args.interval}\nTimeout: {args.timeout}\nPackets: {args.packets}")
    ping(sys.argv[1], timeout)
