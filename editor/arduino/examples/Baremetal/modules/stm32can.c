#include "STM32_CAN.h"

extern "C" uint8_t init_stm32can(int);
extern "C" uint8_t write_stm32can(uint8_t,uint32_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t);
extern "C" uint8_t read_stm32can(uint32_t*, uint8_t*, uint8_t*, uint8_t*, uint8_t*, uint8_t*, uint8_t*, uint8_t*, uint8_t*);

STM32_CAN Can( CAN1, ALT_2 );  //Use PD0/1 pins for CAN1.
//STM32_CAN Can1( CAN1, DEF );  //Use PA11/12 pins for CAN1.
//STM32_CAN Can( CAN1, ALT );  //Use PB8/9 pins for CAN1.
//STM32_CAN Can( CAN2, DEF );  //Use PB12/13 pins for CAN2.
//STM32_CAN Can( CAN2, ALT );  //Use PB5/6 pins for CAN2
//STM32_CAN Can( CAN3, DEF );  //Use PA8/15 pins for CAN3.
//STM32_CAN Can( CAN3, ALT );  //Use PB3/4 pins for CAN3

CAN_message_t CAN1_TX_msg;
CAN_message_t CAN2_TX_msg;
CAN_message_t CAN_RX_msg;

uint8_t init_stm32can(int baudrate)
{   

    Can.begin();
    Can.setBaudRate(baudrate);
	//Can1.begin();
    //Can1.setBaudRate(baudrate);
    return 1;
}

uint8_t write_stm32can(	uint8_t ch,
						uint32_t id,
						uint8_t d0, 
						uint8_t d1,
						uint8_t d2, 
						uint8_t d3, 
						uint8_t d4, 
						uint8_t d5, 
						uint8_t d6,
						uint8_t d7)
{	
	if(ch == 1){
		CAN1_TX_msg.id 				= id;
		CAN1_TX_msg.flags.extended 		= 1;  	// To enable extended ID.
		CAN1_TX_msg.len 			= 8;
		CAN1_TX_msg.buf[0] 	=  d0;
		CAN1_TX_msg.buf[1] 	=  d1;
		CAN1_TX_msg.buf[2] 	=  d2;
		CAN1_TX_msg.buf[3] 	=  d3;
		CAN1_TX_msg.buf[4] 	=  d4;
		CAN1_TX_msg.buf[5] 	=  d5;
		CAN1_TX_msg.buf[6] 	=  d6;
		CAN1_TX_msg.buf[7] 	=  d7;
		
		if (!Can.write(CAN1_TX_msg))
		{
			return 0;
		}
	}
	
	if(ch == 2){
		CAN2_TX_msg.id 				= id;
		CAN2_TX_msg.flags.extended 		= 1;  	// To enable extended ID.
		CAN2_TX_msg.len 			= 8;
		CAN2_TX_msg.buf[0] 	=  d0;
		CAN2_TX_msg.buf[1] 	=  d1;
		CAN2_TX_msg.buf[2] 	=  d2;
		CAN2_TX_msg.buf[3] 	=  d3;
		CAN2_TX_msg.buf[4] 	=  d4;
		CAN2_TX_msg.buf[5] 	=  d5;
		CAN2_TX_msg.buf[6] 	=  d6;
		CAN2_TX_msg.buf[7] 	=  d7;
		
		/*if (!Can1.write(CAN2_TX_msg))
		{
			return 0;
		}*/
	}
	return 1;

}

uint8_t read_stm32can(uint32_t* id, 
					uint8_t* d0, 
					uint8_t* d1, 
					uint8_t* d2, 
					uint8_t* d3, 
					uint8_t* d4, 
					uint8_t* d5, 
					uint8_t* d6, 
					uint8_t* d7)
{
    if (Can.read(CAN_RX_msg)) {
        // Assuming id is a pointer to a uint32_t, and CAN_RX_msg.id is uint32_t
        *id = CAN_RX_msg.id;
        *d0 = CAN_RX_msg.buf[0];
        *d1 = CAN_RX_msg.buf[1];		
        *d2 = CAN_RX_msg.buf[2];
	*d3 = CAN_RX_msg.buf[3];
        *d4 = CAN_RX_msg.buf[4];
        *d5 = CAN_RX_msg.buf[5];
        *d6 = CAN_RX_msg.buf[6];
        *d7 = CAN_RX_msg.buf[7];
        return 1;
    }
    return 0;
}
