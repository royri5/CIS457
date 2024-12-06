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

ICMP_ECHO_REQUEST = 8

# checksum, ignore it
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

# here we go baby, this is where the magic happens
# looks for a reply on socket, 
def receiveOnePing(mySocket, ID, timeout, destAddr): # TODO: print regular info/calculate rtt, print error message when host is unknown, report timeout, report warning when recieving foreign ICMP packets
  timeLeft = timeout
  # holder vars
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
        # TASK: ADDING SEQUENCE NUMBERS
        # make sure to print what seq num timed out, use data from pkt to get seq num
        print ("Timeout")
        return None   # timeout
    else:
      # TASK: FOREIGN ICMP PACKETS
      # TODO: if pkt does not contain the proper pid, ignore it, use getpid() to compare
      # TODO: make sure to update timeLeft, maybe
      # if 
      # timeLeft = timeLeft - howLongInSelect
      # continue
      #
      break
  # CONTEXT: Wow! We just got a packet back! Let's see what's inside it!
  # just checkin how long it took to get here
  timeReceived = time()
  # let's grab that packet and where it came from
  recPacket,addr = mySocket.recvfrom(1024)
  ## BEGIN: your code

  # open your heart to your code
  # it doesn't need to be so cold...

  # now that we have the packet, we have the assignment specified task to do
  # TASK: EXTRACT THE IP AND ICMP DETAILS
  # this segment of code primarily extracts the right IP or ICMP fields/values/data from the packet
  # and prints them out
  # this is the section where the continuous printing of data is done and extracted

  ## Fetch the IP header fields
  ## Fetch the ICMP header fields

  # TASK: CALCULATING THE RTT

  # TASK: PRINT ROUTINE INFO (Remote IP address, ICMP sequence, TTL, and RTT)
  print(f"reply from {remote_ip}: icmp_seq={icmp_seq} ttl={ttl} time={rtt} ms")
  ## END: your code

  # TASK: RETURN RTT ONLY for summary later
  return 0

# this func sends the packet, don't really need to do much
# TASK: ADDING SEQUENCE NUMBERS
def sendOnePing(mySocket, destAddr, ID): # TODO: modify how seq is handled for packet loss detection, accept seq num as arg
  
  # ICMP header fields: 
  #    type      (1 byte) 
  #    code      (1 byte)
  #    checksum  (2 bytes)
  #    id        (2 bytes)
  #    sequence  (2 bytes)
  
  # Make a dummy header with 0 checksum
  myChecksum = 0
  # TASK: ADDING SEQUENCE NUMBERS
  header = pack("bbHHH", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
  data = pack("d", time())
  # calculate the checksum on the header and dummy data
  myChecksum = checksum(header+data)
  # TASK: ADDING SEQUENCE NUMBERS
  header = pack("bbHHH", ICMP_ECHO_REQUEST, 0, htons(myChecksum), ID, 1)
  packet = header+data  
  mySocket.sendto(packet, (destAddr, 1))

# this handles the network stuff, don't need to mess with that
# but it also provides an entry point to our other two ping functions
# and it can be used in our prints to show rtt
def doOnePing(destAddr, timeout): # TODO: modify how sendoneping is called for seq nums, modify how doOnePing is called for seq nums
  icmp = getprotobyname("icmp")
  mySocket = socket(AF_INET, SOCK_RAW, icmp)
  # Use the lowest 16-bit of the PID
  myID = getpid() & 0xFFFF
  # TASK: ADDING SEQUENCE NUMBERS
  sendOnePing(mySocket, destAddr, myID)
  rtt = receiveOnePing(mySocket, myID, timeout, destAddr)
  mySocket.close()
  return rtt

# basically just an entry point to do one ping that repeats 
# and handles end of prog functionality
def ping(host, timeout): # TODO: implement args in func call, handle arguments here, implement sequence numbers, implement the summary when the prog ends here
  #holder vars
  num_pkts_transmitted = 0
  num_pkts_received = None
  min_rtt = None
  max_rtt = None
  avg_rtt = None
  # interval arg functionality
  interval = 1
  if args.interval:
    interval = args.interval
  # packets arg functionality
  num_to_send = None
  if args.packets:
    num_to_send = args.packets
  try:
    dest = gethostbyname(host)
    print (f"PING {host} ({dest}) ")
    while True:
      # packets arg functionality
      if num_to_send is not None:
        if num_pkts_transmitted == num_to_send:
          break
      # TASK: ADDING SEQUENCE NUMBERS
      # modify call and implement seq nums
      doOnePing(dest, timeout)
      num_pkts_transmitted += 1
      sleep(interval)
  except Exception as e:
    print(f"Exception: {e}")
    # MAYBE?? RETURN HERE??
    return
  except KeyboardInterrupt:
    # still want stats even if we go to completion with -n option
    pass
    #print(f"\n--- ping statistics ---")
    #print(f"{num_pkts_transmitted} packets transmitted\n{num_pkts_received} packets received\nMinimum Round Trip Time: {min_rtt} ms\nMaximum Round Trip Time: {max_rtt} ms\nAverage Round Trip Time: {avg_rtt} ms")
    # TASK: SUMMARY INFO PRINT/calculation
  finally:
    print(f"\n--- ping statistics ---")
    print(f"{num_pkts_transmitted} packets transmitted\n{num_pkts_received} packets received\nMinimum Round Trip Time: {min_rtt} ms\nMaximum Round Trip Time: {max_rtt} ms\nAverage Round Trip Time: {avg_rtt} ms")
    return
  

# probably will need to modify this to accept command line args and options
# use a library, make sure to check the assignment tho
if __name__ == "__main__": # TODO: ensure print is to spec for output OSX, implement passing command line args to ping for it to handle
  #holder vars
  # timeout arg functionality
  timeout = 1
  if args.timeout:
    timeout = args.timeout

  if len(sys.argv) < 2:
    print(f"Use {sys.argv[0]} hostname")
  else:
    # test printing for arguments
    print(f"Interval: {args.interval}\nTimeout: {args.timeout}\nPackets: {args.packets}")
    ping(sys.argv[1], timeout)
