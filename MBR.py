import os
import struct
import time
import random
from PARTICION import Partition

class MBR:
    FORMAT = 'i d i c'
    SIZE = struct.calcsize(FORMAT)+Partition.SIZE*4

    def __init__(self, params):
        unit = params.get('unit', 'M').upper()
        size = params['size']

        if unit == 'K':
            self.mbr_tamano = size * 1024
        elif unit == 'M':
            self.mbr_tamano = size * 1024 * 1024
        else:
            raise ValueError(f"Invalid unit: {unit}")

        self.mbr_fecha_creacion = time.time()
        self.mbr_dsk_signature = random.randint(1, 1000000)
        self.fit = params.get('fit', 'FF').upper()
        #create dict with random values for size,path, name
        ex = {'size': 10, 'path': 'path', 'name': 'empty'}
        #create list of 4 partitions
        self.particiones = [Partition(ex), Partition(ex), Partition(ex), Partition(ex)]
        
        #print("\n_____________________MBR CREADO__________________________________________________")
        #from prettytable import PrettyTable
        #table = PrettyTable()
        #table.field_names = ["Size", "Date", "Sig.", "Fit"]
        #table.add_row([self.mbr_tamano, self.mbr_fecha_creacion, self.mbr_dsk_signature, self.fit])
        #print(table)
        #print("___________________________________________________________________________________\n")

        if self.fit not in ['BF', 'FF', 'WF']:
            raise ValueError(f"Invalid fit type: {self.fit}")
        
        
        
        
        
    def __str__(self):
        return f"MBR: size={self.mbr_tamano}, date={self.mbr_fecha_creacion}, signature={self.mbr_dsk_signature}, fit={self.fit}, partitions={self.particiones[0]}, {self.particiones[1]}, {self.particiones[2]}, {self.particiones[3]}"

    def pack(self):
        fit_char = self.fit[0].encode()  # Take the first character of fit type and encode it
        packed_mbr = struct.pack(self.FORMAT, self.mbr_tamano, self.mbr_fecha_creacion, self.mbr_dsk_signature, fit_char)
        #do this for packni the partitions packed_objetos = b''.join([obj.pack() for obj in self.objetos])
        packed_objetos = b''.join([obj.pack() for obj in self.particiones])
        #print("este es el pack de particiones")
        #print(self.particiones[0])
        
        return packed_mbr+packed_objetos

    @classmethod
    def unpack(cls, data):
        print("\n✉️  unpacking MBR...")
        unpacked_data = struct.unpack(cls.FORMAT, data[:struct.calcsize(cls.FORMAT)])
        #print("**************Unpacked MBR Data:", unpacked_data)
        ex = {'size': 5, 'path': 'path', 'name': 'name'}
        mbr = cls(ex) # first two are from 'example' class  
        mbr.mbr_fecha_creacion = 0
        mbr.mbr_tamano = unpacked_data[0]
        mbr.mbr_fecha_creacion = unpacked_data[1]
        mbr.mbr_dsk_signature = unpacked_data[2]
        fit_char = unpacked_data[3].decode()  # Decode the fit character
        fit_map = {'B': 'BF', 'F': 'FF', 'W': 'WF', 'N': 'NF'}
        mbr.fit = fit_map[fit_char]
        ex = {'size': 10, 'path': 'path', 'name': 'name'}
        #create list of 4 partitions
        mbr.particiones = [Partition(ex), Partition(ex), Partition(ex), Partition(ex)]

        #do this for unpacking the partitions temp2 = example(0,0) temp2 = example.unpack(data[struct.calcsize(cls.FORMAT)+example.SIZE:struct.calcsize(cls.FORMAT)+example.SIZE*2])
        temp = Partition.unpack(data[struct.calcsize(cls.FORMAT):struct.calcsize(cls.FORMAT) + Partition.SIZE])
        temp2 = Partition.unpack(data[struct.calcsize(cls.FORMAT)+Partition.SIZE:struct.calcsize(cls.FORMAT)+Partition.SIZE*2])
        temp3 = Partition.unpack(data[struct.calcsize(cls.FORMAT)+Partition.SIZE*2:struct.calcsize(cls.FORMAT)+Partition.SIZE*3])
        temp4 = Partition.unpack(data[struct.calcsize(cls.FORMAT)+Partition.SIZE*3:struct.calcsize(cls.FORMAT)+Partition.SIZE*4])
        mbr.particiones[0] = temp
        mbr.particiones[1] = temp2
        mbr.particiones[2] = temp3
        mbr.particiones[3] = temp4
        
        
        return mbr    
