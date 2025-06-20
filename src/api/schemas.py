from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    numcli: str
    nomcli: Optional[str] = None
    calle: Optional[str] = None
    numext: Optional[str] = None
    colonia: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    cp: Optional[str] = None
    telefono: Optional[str] = None
    fax: Optional[str] = None
    clasif: Optional[str] = None
    ventano: Optional[Decimal] = None
    ultvent: Optional[date] = None
    atvent: Optional[str] = None
    atcobr: Optional[str] = None
    email1: Optional[str] = None
    email2: Optional[str] = None
    rfc: Optional[str] = None
    limcred: Optional[Decimal] = None
    saldo: Optional[Decimal] = None
    pjedesc: Optional[Decimal] = None
    diascred: Optional[int] = None
    precioutil: Optional[str] = None
    recepfac: Optional[str] = None
    pagofac: Optional[str] = None
    obs: Optional[str] = None
    numcta: Optional[str] = None
    uid: Optional[int] = None
    numvend: Optional[str] = None
    obligareq: Optional[bool] = None
    suspendido: Optional[bool] = None
    direnvio: Optional[str] = None
    otrosdatos: Optional[str] = None
    impuesto1: Optional[Decimal] = None
    retencion1: Optional[Decimal] = None
    retencion2: Optional[Decimal] = None
    permitecod: Optional[bool] = None
    llavecred: Optional[bool] = None
    pais: Optional[str] = None
    clavecli: Optional[str] = None
    curp: Optional[str] = None
    nomcomer: Optional[str] = None
    cfgdatdoc: Optional[str] = None
    datosfe: Optional[str] = None
    statusweb: Optional[int] = None
    claveweb: Optional[str] = None
    numzona: Optional[str] = None
    metodopago: Optional[str] = None
    metodousar: Optional[str] = None
    numint: Optional[str] = None
    usocfdi: Optional[str] = None
    formapago: Optional[str] = None
    implocal: Optional[str] = None
    condpago: Optional[str] = None
    emailtw: Optional[str] = None
    numidtrib: Optional[str] = None
    idregimen: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    numart: str
    desc_product: Optional[str] = None
    codigo: Optional[str] = None
    unidad: Optional[str] = None
    unidefa: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    linea: Optional[str] = None
    familia: Optional[str] = None
    categoria: Optional[str] = None
    numdep: Optional[str] = None
    valdep: Optional[str] = None
    ubica: Optional[str] = None
    series_control: Optional[bool] = None
    impuesto1: Optional[Decimal] = None
    impuesto2: Optional[Decimal] = None
    numprov: Optional[str] = None
    numprov1: Optional[str] = None
    numprov2: Optional[str] = None
    numprov3: Optional[str] = None
    ultcomp: Optional[date] = None
    ultcomp1: Optional[date] = None
    ultcomp2: Optional[date] = None
    ultcomp3: Optional[date] = None
    ultvent: Optional[date] = None
    existencia: Optional[Decimal] = None
    minimo: Optional[Decimal] = None
    maximo: Optional[Decimal] = None
    reorden: Optional[Decimal] = None
    divisa: Optional[str] = None
    precio1: Optional[Decimal] = None
    precio2: Optional[Decimal] = None
    precio3: Optional[Decimal] = None
    precio4: Optional[Decimal] = None
    precio5: Optional[Decimal] = None
    factor1: Optional[Decimal] = None
    factor2: Optional[Decimal] = None
    factor3: Optional[Decimal] = None
    factor4: Optional[Decimal] = None
    factor5: Optional[Decimal] = None
    ultcosto: Optional[Decimal] = None
    ultcosto1: Optional[Decimal] = None
    ultcosto2: Optional[Decimal] = None
    ultcosto3: Optional[Decimal] = None
    maxcosto: Optional[Decimal] = None
    costoactua: Optional[Decimal] = None
    costopro: Optional[Decimal] = None
    ventano: Optional[Decimal] = None
    ventanoqty: Optional[Decimal] = None
    activo: Optional[bool] = None
    ultmaxcost: Optional[date] = None
    ultactcost: Optional[date] = None
    compano: Optional[Decimal] = None
    companoqty: Optional[Decimal] = None
    repyy: Optional[bool] = None
    cant_defa: Optional[int] = None
    excento: Optional[bool] = None
    preciopub: Optional[Decimal] = None
    preciof: Optional[bool] = None
    servicio: Optional[bool] = None
    fechamod: Optional[date] = None
    obs: Optional[str] = None
    usacaduc: Optional[bool] = None
    usalotes: Optional[bool] = None
    ventacorte: Optional[Decimal] = None
    eskit: Optional[bool] = None
    uid: Optional[int] = None
    otrosdatos: Optional[str] = None
    pjedesc: Optional[Decimal] = None
    oferta: Optional[Decimal] = None
    insumo: Optional[bool] = None
    peso: Optional[Decimal] = None
    largo: Optional[Decimal] = None
    ancho: Optional[Decimal] = None
    altura: Optional[Decimal] = None
    cantxcj: Optional[int] = None
    foto: Optional[str] = None
    fotos: Optional[str] = None
    idmarca: Optional[str] = None
    preciov2: Optional[Decimal] = None
    preciov3: Optional[Decimal] = None
    preciov4: Optional[Decimal] = None
    preciov5: Optional[Decimal] = None
    ppubv2: Optional[Decimal] = None
    ppubv3: Optional[Decimal] = None
    ppubv4: Optional[Decimal] = None
    ppubv5: Optional[Decimal] = None
    vol2: Optional[Decimal] = None
    vol3: Optional[Decimal] = None
    vol4: Optional[Decimal] = None
    vol5: Optional[Decimal] = None
    statusweb: Optional[int] = None
    clavesat: Optional[str] = None
    implocal: Optional[bool] = None
    fracaranc: Optional[str] = None
    matpelig: Optional[str] = None
    embalaje: Optional[str] = None
    guiaid: Optional[str] = None
    guiaiddesc: Optional[str] = None
    esmatpelig: Optional[bool] = None
    factorv2: Optional[Decimal] = None
    factorv3: Optional[Decimal] = None
    factorv4: Optional[Decimal] = None
    factorv5: Optional[Decimal] = None
    fraccok: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

class MovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    tipodoc: Optional[str] = None
    numdoc: Optional[str] = None
    numpar: Optional[str] = None
    numart: Optional[str] = None
    precio: Optional[Decimal] = None
    costo: Optional[Decimal] = None
    costo2: Optional[Decimal] = None
    costopro: Optional[Decimal] = None
    cant: Optional[Decimal] = None
    pend: Optional[Decimal] = None
    pendocant: Optional[Decimal] = None
    empaque: Optional[Decimal] = None
    devueltos: Optional[Decimal] = None
    pjedesc: Optional[Decimal] = None
    impuesto1: Optional[Decimal] = None
    impuesto2: Optional[Decimal] = None
    unidad: Optional[str] = None
    docant: Optional[str] = None
    obs: Optional[str] = None
    nseries: Optional[str] = None
    capaskit: Optional[str] = None
    pjedesc2: Optional[Decimal] = None
    pjedesc3: Optional[Decimal] = None
    pjedesc4: Optional[Decimal] = None
    lote: Optional[str] = None
    pjedesc1: Optional[Decimal] = None
    promoid: Optional[int] = None
    pendcanc: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

class CustomerSummary(BaseModel):
    numcli: str
    nomcli: Optional[str] = None
    ciudad: Optional[str] = None
    ventano: Optional[Decimal] = None
    saldo: Optional[Decimal] = None
    ultvent: Optional[date] = None

class ProductSummary(BaseModel):
    numart: str
    desc_product: Optional[str] = None
    marca: Optional[str] = None
    precio1: Optional[Decimal] = None
    existencia: Optional[Decimal] = None
    activo: Optional[bool] = None