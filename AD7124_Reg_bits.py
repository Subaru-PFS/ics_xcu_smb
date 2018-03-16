#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 22 15:29:23 2018

@author: pi

Dictionary of AD7124 Register bits
"""

""" Communication Register bits """


def AD7124_COMM_REG_WEN(): return (0 << 7)


def AD7124_COMM_REG_WR(): return (0 << 6)


def AD7124_COMM_REG_RD(): return (1 << 6)


def AD7124_COMM_REG_RA(x): return ((x) & 0x3F)


""" Status Register bits """


def AD7124_STATUS_REG_RDY(): return (1 << 7)


def AD7124_STATUS_REG_ERROR_FLAG(): return (1 << 6)


def AD7124_STATUS_REG_POR_FLAG(): return (1 << 4)


def AD7124_STATUS_REG_CH_ACTIVE(x): return ((x) & 0xF)


""" ADC_Control Register bits """


def AD7124_ADC_CTRL_REG_DOUT_RDY_DEL(): return (1 << 12)


def AD7124_ADC_CTRL_REG_CONT_READ(): return (1 << 11)


def AD7124_ADC_CTRL_REG_DATA_STATUS(): return (1 << 10)


def AD7124_ADC_CTRL_REG_CS_EN(): return (1 << 9)


def AD7124_ADC_CTRL_REG_REF_EN(): return (1 << 8)


def AD7124_ADC_CTRL_REG_POWER_MODE(x): return (((x) & 0x3) << 6)


def AD7124_ADC_CTRL_REG_MODE(x): return (((x) & 0xF) << 2)


def AD7124_ADC_CTRL_REG_CLK_SEL(x): return (((x) & 0x3) << 0)


""" IO_Control_1 Register bits """


def AD7124_IO_CTRL1_REG_GPIO_DAT2(): return (1 << 23)


def AD7124_IO_CTRL1_REG_GPIO_DAT1(): return (1 << 22)


def AD7124_IO_CTRL1_REG_GPIO_CTRL2(): return (1 << 19)


def AD7124_IO_CTRL1_REG_GPIO_CTRL1(): return (1 << 18)


def AD7124_IO_CTRL1_REG_PDSW(): return (1 << 15)


def AD7124_IO_CTRL1_REG_IOUT1(x): return (((x) & 0x7) << 11)


def AD7124_IO_CTRL1_REG_IOUT0(x): return (((x) & 0x7) << 8)


def AD7124_IO_CTRL1_REG_IOUT_CH1(x): return (((x) & 0xF) << 4)


def AD7124_IO_CTRL1_REG_IOUT_CH0(x): return (((x) & 0xF) << 0)


""" IO_Control_1 AD7124-8 specific bits """


def AD7124_8_IO_CTRL1_REG_GPIO_DAT4(): return (1 << 23)


def AD7124_8_IO_CTRL1_REG_GPIO_DAT3(): return (1 << 22)


def AD7124_8_IO_CTRL1_REG_GPIO_DAT2(): return (1 << 21)


def AD7124_8_IO_CTRL1_REG_GPIO_DAT1(): return (1 << 20)


def AD7124_8_IO_CTRL1_REG_GPIO_CTRL4(): return (1 << 19)


def AD7124_8_IO_CTRL1_REG_GPIO_CTRL3(): return (1 << 18)


def AD7124_8_IO_CTRL1_REG_GPIO_CTRL2(): return (1 << 17)


def AD7124_8_IO_CTRL1_REG_GPIO_CTRL1(): return (1 << 16)


""" IO_Control_2 Register bits """


def AD7124_IO_CTRL2_REG_GPIO_VBIAS7(): return (1 << 15)


def AD7124_IO_CTRL2_REG_GPIO_VBIAS6(): return (1 << 14)


def AD7124_IO_CTRL2_REG_GPIO_VBIAS5(): return (1 << 11)


def AD7124_IO_CTRL2_REG_GPIO_VBIAS4(): return (1 << 10)


def AD7124_IO_CTRL2_REG_GPIO_VBIAS3(): return (1 << 5)


def AD7124_IO_CTRL2_REG_GPIO_VBIAS2(): return (1 << 4)


def AD7124_IO_CTRL2_REG_GPIO_VBIAS1(): return (1 << 1)


def AD7124_IO_CTRL2_REG_GPIO_VBIAS0(): return (1 << 0)


""" IO_Control_2 AD7124-8 specific bits """


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS15(): return (1 << 15)


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS14(): return (1 << 14)


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS13(): return (1 << 13)


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS12(): return (1 << 12)


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS11(): return (1 << 11)


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS10(): return (1 << 10)


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS9(): return (1 << 9)


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS8(): return (1 << 8)


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS7(): return (1 << 7)


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS6(): return (1 << 6)


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS5(): return (1 << 5)


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS4(): return (1 << 4)


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS3(): return (1 << 3)


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS2(): return (1 << 2)


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS1(): return (1 << 1)


def AD7124_8_IO_CTRL2_REG_GPIO_VBIAS0(): return (1 << 0)


""" ID Register bits """


def AD7124_ID_REG_DEVICE_ID(x): return (((x) & 0xF) << 4)


def AD7124_ID_REG_SILICON_REV(x): return (((x) & 0xF) << 0)


""" Error Register bits """


def AD7124_ERR_REG_LDO_CAP_ERR(): return (1 << 19)


def AD7124_ERR_REG_ADC_CAL_ERR(): return (1 << 18)


def AD7124_ERR_REG_ADC_CONV_ERR(): return (1 << 17)


def AD7124_ERR_REG_ADC_SAT_ERR(): return (1 << 16)


def AD7124_ERR_REG_AINP_OV_ERR(): return (1 << 15)


def AD7124_ERR_REG_AINP_UV_ERR(): return (1 << 14)


def AD7124_ERR_REG_AINM_OV_ERR(): return (1 << 13)


def AD7124_ERR_REG_AINM_UV_ERR(): return (1 << 12)


def AD7124_ERR_REG_REF_DET_ERR(): return (1 << 11)


def AD7124_ERR_REG_DLDO_PSM_ERR(): return (1 << 9)


def AD7124_ERR_REG_ALDO_PSM_ERR(): return (1 << 7)


def AD7124_ERR_REG_SPI_IGNORE_ERR(): return (1 << 6)


def AD7124_ERR_REG_SPI_SLCK_CNT_ERR(): return (1 << 5)


def AD7124_ERR_REG_SPI_READ_ERR(): return (1 << 4)


def AD7124_ERR_REG_SPI_WRITE_ERR(): return (1 << 3)


def AD7124_ERR_REG_SPI_CRC_ERR(): return (1 << 2)


def AD7124_ERR_REG_MM_CRC_ERR(): return (1 << 1)


""" Error_En Register bits """


def AD7124_ERREN_REG_MCLK_CNT_EN(): return (1 << 22)


def AD7124_ERREN_REG_LDO_CAP_CHK_TEST_EN(): return (1 << 21)


def AD7124_ERREN_REG_LDO_CAP_CHK(x): return (((x) & 0x3) << 19)


def AD7124_ERREN_REG_ADC_CAL_ERR_EN(): return (1 << 18)


def AD7124_ERREN_REG_ADC_CONV_ERR_EN(): return (1 << 17)


def AD7124_ERREN_REG_ADC_SAT_ERR_EN(): return (1 << 16)


def AD7124_ERREN_REG_AINP_OV_ERR_EN(): return (1 << 15)


def AD7124_ERREN_REG_AINP_UV_ERR_EN(): return (1 << 14)


def AD7124_ERREN_REG_AINM_OV_ERR_EN(): return (1 << 13)


def AD7124_ERREN_REG_AINM_UV_ERR_EN(): return (1 << 12)


def AD7124_ERREN_REG_REF_DET_ERR_EN(): return (1 << 11)


def AD7124_ERREN_REG_DLDO_PSM_TRIP_TEST_EN(): return (1 << 10)


def AD7124_ERREN_REG_DLDO_PSM_ERR_ERR(): return (1 << 9)


def AD7124_ERREN_REG_ALDO_PSM_TRIP_TEST_EN(): return (1 << 8)


def AD7124_ERREN_REG_ALDO_PSM_ERR_EN(): return (1 << 7)


def AD7124_ERREN_REG_SPI_IGNORE_ERR_EN(): return (1 << 6)


def AD7124_ERREN_REG_SPI_SCLK_CNT_ERR_EN(): return (1 << 5)


def AD7124_ERREN_REG_SPI_READ_ERR_EN(): return (1 << 4)


def AD7124_ERREN_REG_SPI_WRITE_ERR_EN(): return (1 << 3)


def AD7124_ERREN_REG_SPI_CRC_ERR_EN(): return (1 << 2)


def AD7124_ERREN_REG_MM_CRC_ERR_EN(): return (1 << 1)


""" Channel Registers 0-15 bits """


def AD7124_CH_MAP_REG_CH_ENABLE(): return (1 << 15)


def AD7124_CH_MAP_REG_SETUP(x): return (((x) & 0x7) << 12)


def AD7124_CH_MAP_REG_AINP(x): return (((x) & 0x1F) << 5)


def AD7124_CH_MAP_REG_AINM(x): return (((x) & 0x1F) << 0)


""" Configuration Registers 0-7 bits """


def AD7124_CFG_REG_BIPOLAR(): return (1 << 11)


def AD7124_CFG_REG_BURNOUT(x): return (((x) & 0x3) << 9)


def AD7124_CFG_REG_REF_BUFP(): return (1 << 8)


def AD7124_CFG_REG_REF_BUFM(): return (1 << 7)


def AD7124_CFG_REG_AIN_BUFP(): return (1 << 6)


def AD7124_CFG_REG_AINN_BUFM(): return (1 << 5)


def AD7124_CFG_REG_REF_SEL(x): return ((x) & 0x3) << 3


def AD7124_CFG_REG_PGA(x): return (((x) & 0x7) << 0)


""" Filter Register 0-7 bits """


def AD7124_FILT_REG_FILTER(x): return (((x) & 0x7) << 21)


def AD7124_FILT_REG_REJ60(): return (1 << 20)


def AD7124_FILT_REG_POST_FILTER(x): return (((x) & 0x7) << 17)


def AD7124_FILT_REG_SINGLE_CYCLE(): return (1 << 16)


def AD7124_FILT_REG_FS(x): return (((x) & 0x7FF) << 0)
