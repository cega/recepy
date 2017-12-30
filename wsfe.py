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

import logging
import sys
from datetime import datetime
from json import dumps

from zeep import helpers

from libs import utility, web_service
from wsaa import WSAA

__author__ = 'Alejandro Naifuino (alenaifuino@gmail.com)'
__copyright__ = 'Copyright (C) 2017 Alejandro Naifuino'
__license__ = 'GPL 3.0'
__version__ = '0.3.2'


class WSFE(web_service.BaseWebService):
    """
    Clase que se usa de interfaz para el Web Service de Factura Electrónica
    de AFIP
    """
    def __init__(self, config):
        self.config = config
        self.token = None
        self.sign = None
        super().__init__(self.config, '<string>.json')

    def __request_fe(self, req_type):
        """
        Método genérico que realiza la solicitud según el req_type definido
        """
        # Valido que el servicio de AFIP este funcionando
        if self.dummy('FEDummy'):
            raise SystemExit('El servicio de AFIP no se encuentra disponible')

        # Formateo el tipo de requerimiento
        req_type = req_type.upper()

        # Establezco el nombre del servicio que será llamado
        service_name = 'FE' + req_type + 'Solicitar'

        # Defino los parámetros de autenticación
        params = {
            'Auth': {
                'Token': self.token,
                'Sign': self.sign,
                'Cuit': self.config['cuit']
            }
        }

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
            extra = {
                'Periodo': '',
                'Orden': ''
            }

        # Actualizo el diccionario de parámetros
        params.update(extra)

        # Obtengo la respuesta del WSDL de AFIP
        response = self.soap_connect(
            self.config['ws_wsdl'], service_name, params)

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

    def __request_param(self):
        """
        Método genérico que realiza la solicitud al método de AFIP definido
        según service_name
        """
        service_names = {
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
        if self.config['parameter'] not in service_names.keys():
            raise SystemExit('El parámetro no está soportado por el Web '
                             'Service de Factura Electrónica')
        else:
            service_name = service_names[self.config['parameter']]

        # Valido que el servicio de AFIP esté funcionando
        if self.dummy('FEDummy'):
            raise SystemExit('El servicio de AFIP no se encuentra disponible')

        # Defino los parámetros de autenticación
        params = {
            'Auth': {
                'Token': self.token,
                'Sign': self.sign,
                'Cuit': self.config['cuit']
            }
        }

        # Agrego los parámetros adicionales según el método solicitado
        if service_name == 'FEParamGetCotizacion':
            params.update({'MonId': self.config['currency_id']})

        # Obtengo la respuesta del WSDL de AFIP
        response = self.soap_connect(
            self.config['ws_wsdl'], service_name, params)

        # Lo transformo a JSON
        json_response = dumps(response, indent=2, ensure_ascii=False)

        # Genero el archivo con la respuesta de AFIP
        output = self.get_output_path(name=self.config['parameter'])
        with open(output, 'w') as file:
            file.write(json_response)

        return json_response

    def request(self, option, ticket_data):
        """
        Método wrapper que define a qué método se llama en base a option
        """
        self.token = ticket_data['token']
        self.sign = ticket_data['sign']

        if option == 'parameter':
            self.__request_param()
        elif option == 'request':
            self.__request_param()


def main():
    """
    Función utilizada para la ejecución del script por línea de comandos
    """
    # Obtengo los parámetros pasados por línea de comandos
    args = utility.cli_parser(__file__, __version__)

    # Obtengo los datos de configuración
    try:
        config_data = utility.get_config_data(args)
    except ValueError as error:
        raise SystemExit(error)

    # Muestro las opciones de configuración via stdout
    if config_data['debug']:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        logging.info('|============  Configuración  ============')
        logging.info('| Certificado:   %s', config_data['certificate'])
        logging.info('| Clave Privada: %s', config_data['private_key'])
        logging.info('| Frase Secreta: %s',
                     '******' if config_data['passphrase'] else None)
        logging.info('| WSAA WSDL:     %s', config_data['wsdl'])
        logging.info('| WS:            %s', config_data['web_service'])
        logging.info('| WS WSDL:       %s', config_data['ws_wsdl'])
        logging.info('|=================  ---  =================')

    # Instancio WSFE para obtener un objeto de Factura Electrónica AFIP
    voucher = WSFE(config_data)

    # Instancio WSAA para obtener un objeto de autenticación y autorización
    wsaa = WSAA(config_data)

    # Obtengo el ticket de autorización de AFIP
    ticket_data = wsaa.get_ticket()

    # Defino el método de conexión
    option = 'parameter' if config_data['parameter'] else 'request'

    # Obtengo los datos solicitados
    voucher.request(option, ticket_data)

    # Imprimo la ubicación del archivo de salida
    print('Respuesta AFIP en: {}'.format(
        voucher.get_output_path(name=config_data['parameter'])))


if __name__ == '__main__':
    main()
