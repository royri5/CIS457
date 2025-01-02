//
// Created by Hans Dulimarta Fall 2024
//
#include <printf.h>
#include "rdt.h"
#include <cstring> // strncpy
#include <queue>

/********* STUDENTS WRITE THE NEXT SEVEN ROUTINES *********/

// globals
int current_seq;
int in_transit_sender;
int expected_seq;
int prev_ack;
// buffer of packets
const int BUFFER_SIZE = 50;
const int WINDOW_SIZE = 4;
int window_start;
int window_end;
int window_flag;
pkt window[WINDOW_SIZE + 1];
pkt buffer[BUFFER_SIZE];
// buffer index
int buffer_index;
int current_pkt_index;

// DONE
int checksum(struct pkt *packet) {
    int sum = 0;
    sum += packet->seqnum;
    sum += packet->acknum;
    for(int i = 0; i < 20; i++) {
        if(packet->payload[i] == '\0') {
            break;
        }
        sum += packet->payload[i];
    }
    return sum;
}

// DONE
void fill_window() {
    // extract packets from buffer to reach window size
    // check if window is full
    if(window_flag == 1 && window_start == window_end) {
        // window is full
        return;
    }
    for(int i=0; i < WINDOW_SIZE; i++) {
        // check if buffer is empty
        if(buffer_index == current_pkt_index) {
            // buffer is empty
            break;
        }
        else {
            // add packet to window
            window_flag = 1; // window is not empty
            window[window_end] = buffer[current_pkt_index];
            // update pkt data
            window[window_end].seqnum = window_end;
            window[window_end].checksum = checksum(&window[window_end]);
            // update buffer index
            current_pkt_index++;
            if(current_pkt_index == BUFFER_SIZE) {
                current_pkt_index = 0;
            }

            int next_window_end = window_end + 1;
            if(next_window_end == WINDOW_SIZE) {
                next_window_end = 0;
            }
            window_end = next_window_end;
            if(window_end == window_start) {
                // window is full
                break;
            }
        }
    }
}

// DONE
void A_send_window(int resend_flag) {
    int first_flag = 0;
    // send packets in window
    if(window_flag == 0) {
        // window is empty
        //printf("A_send_window: Window is empty\n");
        return;
    }
    //printf("A_send_window: Test: window_start: %d, window_end: %d\n", window_start, window_end);
    int window_it = window_start;
    //VVVVV
    for(int i = 0; i < WINDOW_SIZE; i++) {
        if(window_it == WINDOW_SIZE) {
            window_it = 0;
        }
        if(i != 0 && window_it == window_end) {
            // window finished
            break;
        }
        // send packet
        // start timer on first packet
        if(first_flag == 0) {
            starttimer(0, 20.0);
            first_flag = 1;
        }
        in_transit_sender = 1;
        to_network_layer(0, window[window_it]);
        if(resend_flag == 1) {
            printf("A: Resent pkt with seq: %d\n", window[window_it].seqnum);
        } else {
            printf("A: Sent pkt with seq: %d\n", window[window_it].seqnum);
        }
        window_it++;
    }
    // if(in_transit_sender == 1) {
    //     starttimer(0, 20.0);
    // }
}

/* called from layer 5, passed the data to be sent to other side */
// DONE
void A_output(struct msg message) {
    printf("Sender A has a message %s\n", message.data);
    // make pkt
    pkt packet;
    //init
    packet.seqnum = 0; //default
    packet.acknum = 0; //default
    
    //payload
    //copy msg data to payload
    strncpy(packet.payload, message.data, sizeof(packet.payload) - 1);
    packet.checksum = checksum(&packet);
    // add to buffer
    int new_index = buffer_index + 1;
    if(new_index == BUFFER_SIZE) {
        new_index = 0;
    }
    if(new_index == current_pkt_index) {
        // buffer is full
        printf("A: Buffer is full, dropping message\n");
        return;
    }
    buffer[buffer_index] = packet;
    buffer_index = new_index;

    // check that no msg is currently in transit
    if(in_transit_sender == 1) {
        // update logic to loop through buffer
        //printf("A_output: Packets in transit, stored in buffer\n");
        // buffer logic
        return;
    }
    // extract packets from buffer to reach window size
    fill_window();
    // send packets in window
    A_send_window(0);
}


void B_output(struct msg message)  /* need be completed only for extra credit */
{
    printf("B_output is incomplete\n");
    // vvvv push message to application layer (from transport layer)
    //to_network_layer();
}

//void A_dupe_ack() {
//    stoptimer(0);
//    A_send_window(1);
//}

/* called from layer 3, when a packet arrives for layer 4 */
void A_input(struct pkt packet) {
    // checksum
    if(checksum(&packet) != packet.checksum) {
        printf("A: Received corrupt ACK\n");
        return;
    }
    // check if ACK is correct
    // first check (first pkt corrupt)
    if(prev_ack == -1) {
        prev_ack = packet.acknum;
    } else if(prev_ack == packet.acknum) {
        // duplicate ACK
        printf("A: Duplicate ACK %d\n", packet.acknum);
        //A_dupe_ack(); 
        //prev_ack = -1;
        return;
    }

    if(in_transit_sender == 0) {
        // ACK out of order
        printf("A: out of order ACK %d\n", packet.acknum);
        return;
    }

    printf("A: Received ACK with acknum: %d\n", packet.acknum);

    // update window
    int next_window_start = packet.acknum + 1;
    if(next_window_start == WINDOW_SIZE) {
         next_window_start = 0;
    }

    window_start = next_window_start;
    if(next_window_start == window_end) {
        // window finished
        // update window
        stoptimer(0);
        in_transit_sender = 0;
        window_flag = 0;
        // helps with wrapping to reset
        prev_ack = -1;
        // update seq
        //current_seq = window_start;
        fill_window();
        A_send_window(0);

    }

}

/* called when A's timer goes off */
// DONE
void A_timerinterrupt() {
    //printf("A_timerinterrupt is incomplete\n");
    //printf("A_timerinterrupt: Resending pkt seqnum: %d\n", buffer[current_pkt_index].seqnum);
    printf("A: Timeout\n");
    // update window
    // shouldn't add more, only retransmit unacked packets
    //fill_window();
    // resend packets
    A_send_window(1);
    // resend packet
}


/* the following routine will be called once (only) before any other */
/* entity A routines are called. You can use it to do any initialization */
// DONE
void A_init() {
    // transport layer init
    //printf("A_init is incomplete\n");
    // current state
    // seq
    current_seq = 0;
    in_transit_sender = 0;
    buffer_index = 0;
    current_pkt_index = 0;
    window_start = 0;
    window_end = 0;
    prev_ack = -1;
}


/* Note that with simplex transfer from a-to-B, there is no B_output() */

/* called from layer 3, when a packet arrives for layer 4 at B*/
// DONE
void B_input(struct pkt packet) {
    //printf("B_input is incomplete\n");
    //checksum
    if(checksum(&packet) != packet.checksum) {
        printf("B: Received corrupt pkt\n");
        //packet.acknum = 1 - expected_seq;
        packet.acknum = packet.seqnum - 1;
        packet.seqnum = 0;
        // new checksum
        packet.checksum = checksum(&packet);
        to_network_layer(1, packet);
        printf("B: Sent ACK with acknum %d\n", packet.acknum);
        return;
    }
    // check if seq is correct
    if(packet.seqnum != expected_seq) {
        printf("B: Received pkt: %d Out of order\n", packet.seqnum);
        //
        // send ACK
        //packet.acknum = 1 - expected_seq;
        //packet.acknum = packet.seqnum - 1;
        packet.acknum = expected_seq - 1;
        if(packet.acknum == -1) {
            packet.acknum = WINDOW_SIZE - 1;
        }
        packet.seqnum = 0;
        // new checksum
        packet.checksum = checksum(&packet);
        to_network_layer(1, packet);
        printf("B: Sent ACK sent with acknum: %d\n", packet.acknum);
        return;
    }
    pkt ack;
    ack.acknum = packet.seqnum;
    ack.seqnum = 0;
    expected_seq++;
    if(expected_seq == WINDOW_SIZE) {
        expected_seq = 0;
    }
    //ack.checksum = 0; //default
    
    // shouldn't need to copy payload
    ack.payload[0] = '\0';
    ack.checksum = checksum(&ack);

    to_network_layer(1, ack);
    printf("B: Sent ACK sent with acknum: %d\n", ack.acknum);
    printf("B: msg forwarded to application layer: %s\n", packet.payload);
    // vvvv push packet to application layer (from transport layer)
    // to_app_layer(1, packet.payload);
}

/* called when B's timer goes off */
void B_timerinterrupt() {
    printf("B_timerinterrupt is incomplete\n");
}

/* the following rouytine will be called once (only) before any other */
/* entity B routines are called. You can use it to do any initialization */
// DONE
void B_init() {
    //printf("B_init is incomplete\n");

    // current state
    // seq
    expected_seq = 0;
}

