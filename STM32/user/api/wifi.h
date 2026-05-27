#ifndef _WIFI_H_
#define _WIFI_H_

#include "stm32f10x.h"

#define WIFI_RX_MAX_LEN 256
typedef struct {
	uint8_t recvData[WIFI_RX_MAX_LEN];
	uint8_t recvCount;
	uint8_t recvOver;
	uint8_t connectFlag;
}__WIFI_TYPE;

extern __WIFI_TYPE wifi;

void WIFI_Config(void);
void WIFI_Analysis(void);
#endif
