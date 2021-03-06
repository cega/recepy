#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
"""
Módulo que permite consultar los métodos del Web Service de Factura
Electrónica de AFIP

Métodos:
CAE:
    - FECAESolicitar: Método de autorización de comprobantes
        electrónicos por CAE

CAEA:
    - FECAEASolicitar: Método de obtención de CAEA
    - FECAEAConsultar: Método de consulta de CAEA
    - FECAEASinMovimientoInformar: Método para informar CAEA sin
        movimiento
    - FECAEARegInformativo: Método para informar comprobantes emitidos
        con CAEA
    - FECAEASinMovimientoConsultar: Método para consultar CAEA sin
        movimiento

Ambos:
    - FEParamGetTiposCbte: Recuperador de valores referenciales de
        códigos de Tipos de comprobante
    - FEParamGetTiposConcepto: Recuperador de valores referenciales de
        códigos de Tipos de Conceptos
    - FEParamGetTiposDoc: Recuperador de valores referenciales de
        códigos de Tipos de Documentos
    - FEParamGetTiposIva: Recuperador de valores referenciales de
        códigos de Tipos de Alícuotas
    - FEParamGetTiposMonedas: Recuperador de valores referenciales de
        códigos de Tipos de Monedas
    - FEParamGetTiposOpcional: Recuperador de valores referenciales de
        códigos de Tipos de datos Opcionales
    - FEParamGetTiposTributos: Recuperador de valores referenciales de
        códigos de Tipos de Tributos
    - FEParamGetPtosVenta: Recuperador de los puntos de venta asignados
        a Facturación Electrónica que soporten CAE y CAEA vía Web
        Services
    - FEParamGetCotizacion: Recuperador de cotización de moneda
    - FEDummy: Método Dummy para verificación de funcionamiento de
        infraestructura
    - FECompUltimoAutorizado: Recuperador de ultimo valor de
        comprobante registrado
    - FECompTotXRequest: Recuperador de cantidad máxima de registros
        FECAESolicitar / FECAEARegInformativo
    - FECompConsultar: Método para consultar Comprobantes Emitidos y su
        código

Especificación Técnica v2.10 en:
http://www.afip.gob.ar/fe/documentos/manual_desarrollador_COMPG_v2_10.pdf
"""

from json import dumps

from zeep import exceptions

from libs import utility, web_service
from wsaa import WSAA

__author__ = 'Alejandro Naifuino (alenaifuino@gmail.com)'
__copyright__ = 'Copyright (C) 2017 Alejandro Naifuino'
__license__ = 'GPL 3.0'
__version__ = '0.7.1'


class WSFE(web_service.WSBase):
    """
    Clase que se usa de interfaz para el Web Service de Factura Electrónica
    de AFIP
    """

    def __init__(self, config):
        super().__init__(config['debug'], config['ws_wsdl'],
                         config['web_service'])
        self.cuit = utility.get_cuit()
        self.request = 'comprobante' if config['comprobante'] else 'parametro'
        self.option = config[self.request]

        # Establezco el ID de la moneda a cotizar si el método es cotizacion
        if self.request == 'parametro' and self.option == 'cotizacion':
            self.currency_id = config['id']

        # Establezco el tipo de comprobante dependiendo del método seleccionado
        if self.request == 'comprobante':
            if self.option in ('solicitar', 'ultimo_autorizado',
                               'cantidad_registros', 'consultar_comprobante'):
                self.voucher_type = config['tipo']

    def __request_param(self):
        """
        Método genérico que realiza la solicitud a los métodos de AFIP que
        devuelven parámetros
        """
        # Métodos soportados por el web service de Factura Electrónica
        methods = {
            'comprobante': 'FEParamGetTiposCbte',
            'concepto': 'FEParamGetTiposConcepto',
            'documento': 'FEParamGetTiposDoc',
            'iva': 'FEParamGetTiposIva',
            'monedas': 'FEParamGetTiposMonedas',
            'opcional': 'FEParamGetTiposOpcional',
            'tributos': 'FEParamGetTiposTributos',
            'puntos_venta': 'FEParamGetPtosVenta',
            'cotizacion': 'FEParamGetCotizacion',
            'tipos_paises': 'FEParamGetTiposPaises',
        }

        # Valido el nombre del método solicitado y lo asigno si es válido
        if self.option not in methods.keys():
            raise SystemExit('El parámetro no está soportado por el Web '
                             'Service de Factura Electrónica')
        else:
            method = methods[self.option]

        # Establezco el lugar donde se almacenan los datos
        self.set_output_path(output_file=self.option + '.json')

        # Defino los parámetros de autenticación
        params = {
            'Auth': {
                'Token': self.token,
                'Sign': self.sign,
                'Cuit': self.cuit
            }
        }

        # Agrego los parámetros adicionales para el método cotizacion
        if self.option == 'cotizacion':
            params.update({'MonId': self.currency_id})

        # Obtengo la respuesta del WSDL de AFIP
        try:
            response = web_service.soap_connect(self.ws_wsdl, method, params)
        except exceptions.Fault as error:
            raise SystemExit('Error: {} {}'.format(error.code, error.message))

        # Lo transformo a JSON
        json_response = dumps(response, indent=2, ensure_ascii=False)

        # Genero el archivo con la respuesta de AFIP
        with open(self.output, 'w') as file:
            file.write(json_response)

        return json_response

    def __request_fe(self):
        """
        Método genérico que realiza la solicitud según el req_type definido
        """
        # Métodos soportados por el web service de Factura Electrónica
        methods = {
            'solicitar': '',
            'consultar': 'FECAEAConsultar',
            'informar_sin_movimiento': 'FECAEASinMovimientoInformar',
            'consultar_sin_movimiento': 'FECAEASinMovimientoConsultar',
            'informar_comprobantes': 'FECAEARegInformativo',
            'ultimo_autorizado': 'FECompUltimoAutorizado',
            'cantidad_registros': 'FECompTotXRequest',
            'consultar_comprobante': 'FECompConsultar',
        }

        # Valido el nombre del método solicitado y lo asigno si es válido
        if self.option not in methods.keys():
            raise SystemExit('El parámetro no está soportado por el Web '
                             'Service de Factura Electrónica')
        else:
            method = methods[self.option]

        # Establezco el lugar donde se almacenan los datos
        self.set_output_path(output_file=self.option + '.json')

        # Defino los parámetros de autenticación
        params = {
            'Auth': {
                'Token': self.token,
                'Sign': self.sign,
                'Cuit': self.cuit
            }
        }

        # Agrego los parámetros adicionales para el método cotizacion

        # Defino los parámetros adicionales según el tipo de requerimiento
        if req_type == 'FECAESolicitar':
            extra = {
                'FeCAEReq': {
                    'FeCabReq': {
                        'CantReg': '',
                        'PtoVta': '',
                        'CbteTipo': '',
                    },
                    'FeDetReq': {
                        'FECAEDetRequest': {
                            'Concepto': '',
                            'DocTipo': '',
                            'DocNro': '',
                            'CbteDesde': '',
                            'CbteHasta': '',
                            'CbteFch': '',
                            'ImpTotal': '',
                            'ImpTotConc': '',
                            'ImpNeto': '',
                            'ImpOpEx': '',
                            'ImpTrib': '',
                            'ImpIVA': '',
                            'FchServDesde': '',
                            'FchServHasta': '',
                            'FchVtoPago': '',
                            'MonId': '',
                            'MonCotiz': '',
                            'CbtesAsoc': {
                                'CbteAsoc': {
                                    'Tipo': '',
                                    'PtoVta': '',
                                    'Nro': ''
                                }
                            },
                            'Tributos': {
                                'Tributo': {
                                    'Id': '',
                                    'Desc': '',
                                    'BaseImp': '',
                                    'Alic': '',
                                    'Importe': '',
                                }
                            },
                            'Iva': {
                                'AlicIva': {
                                    'Id': '',
                                    'BaseImp': '',
                                    'Importe': '',
                                }
                            },
                            'Opcionales': {
                                'Opcional': {
                                    'Id': '',
                                    'Valor': '',
                                }
                            }
                        }
                    }
                }
            }
        elif req_type == 'FECAEASolicitar' or req_type == 'FECAEAConsultar':
            extra = {'Periodo': '', 'Orden': ''}

        # Actualizo el diccionario de parámetros
        params.update(extra)

        # Obtengo la respuesta del WSDL de AFIP
        try:
            response = web_service.soap_connect(self.ws_wsdl, method, params)
        except exceptions.Fault as error:
            raise SystemExit('Error: {} {}'.format(error.code, error.message))
        '''
        {
            'FECAEASinMovimientoInformar': {
                'PtoVta': '',
                'CAEA': ''
            },
            'FECAEARegInformativo': {
                'FeCAEARegInfReq': {
                    'FeCabReq': {
                        'CantReg': '',
                        'PtoVta': '',
                        'CbteTipo': ''
                    },
                    'FeDetReq': {
                        'FECAEADetRequest': {
                            'Concepto': 'Concepto',
                            'DocTipo': 'DocTipo',
                            'DocNro': 'DocNro',
                            'CbteDesde': 'CbteDesde',
                            'CbteHasta': 'CbteHasta',
                            'CbteFch': 'CbteFch',
                            'ImpTotal': 'ImpTotal',
                            'ImpTotConc': 'ImpTotConc',
                            'ImpNeto': 'ImpNeto',
                            'ImpOpEx': 'ImpOpEx',
                            'ImpIVA': 'ImpIVA',
                            'ImpTrib': 'ImpTrib',
                            'FchServDesde': 'FchServDesde',
                            'FchServHasta': 'FchServHasta',
                            'FchVtoPago': 'FchVtoPago',
                            'MonId': 'MonId',
                            'MonCotiz': 'MonCotiz',
                            'CbtesAsoc': {
                                'CbteAsoc': {
                                    'Tipo': '',
                                    'PtoVta': '',
                                    'Nro': ''
                                }
                            },
                            'Tributos': {
                                'Tributo': {
                                    'Id': '',
                                    'Desc': '',
                                    'BaseImp': '',
                                    'Alic': '',
                                    'Importe': ''
                                }
                            },
                            'Iva': {
                                'AlicIva': {
                                    'Id': '',
                                    'BaseImp': '',
                                    'Importe': ''
                                }
                            },
                            'Opcionales': {
                                'Opcional': {
                                    'Id': '',
                                    'Valor': ''
                                }
                            },
                            'CAEA': ''
                        }
                    }
                }
            },
            'FECAEASinMovimientoConsultar': {
                'CAEA': '',
                'PtoVta': ''
            },
            'FECompUltimoAutorizado': {
                'PtoVta': '',
                'CbteTipo': ''
            },
            'FECompConsultar': {
                'FeCompConsReq': {
                    'CbteTipo': '',
                    'CbteNro': '',
                    'PtoVta': ''
                }
            },
            'FECompTotXRequest': ''
        }
        '''

    def get_request(self):
        """
        Wrapper que define a qué método se llama dependiendo de la opción
        seleccionada validando primero que el web service de AFIP esté activo
        """
        # Valido que el servicio de AFIP esté funcionando
        if self.dummy('FEDummy'):
            raise SystemExit('El servicio de AFIP no se encuentra disponible')

        if self.request == 'parametro':
            self.__request_param()
        elif self.request == 'comprobante':
            self.__request_fe()


def main():
    """
    Función utilizada para la ejecución del script por línea de comandos
    """
    # Obtengo los parámetros pasados por línea de comandos
    args = utility.cli_parser(__version__)

    # Obtengo los datos de configuración
    try:
        config_data = utility.get_config_data(args)
    except ValueError as error:
        raise SystemExit(error)

    # Muestro las opciones de configuración via stdout
    if config_data['debug']:
        utility.print_config(config_data)

    # Instancio WSAA para obtener un objeto de autenticación y autorización
    wsaa = WSAA(config_data)

    # Instancio WSFE para obtener un objeto de Factura Electrónica AFIP
    voucher = WSFE(config_data)

    # Obtengo el ticket de autorización de AFIP
    voucher.token, voucher.sign = wsaa.get_ticket()

    # Obtengo los datos solicitados
    voucher.get_request()

    # Imprimo la ubicación del archivo de salida
    print('Respuesta AFIP en: {}'.format(voucher.output))


if __name__ == '__main__':
    main()
