import os
import struct
import time
import random
class Partition:
    # Using a format to capture size(int), path(string of 100 chars), name(string of 16 chars), unit(char)
    FORMAT = 'i 16s c c i c i'
    SIZE = struct.calcsize(FORMAT)

    def __init__(self, params):
        # Extracting size from params
        self.actual_size = params.get('size')
        
        if self.actual_size < 0:
            raise ValueError("Size must be a positive integer greater than 0")

        # Extracting path from params

        # Extracting name from params
        self.name = params.get('name')
        if not self.name:
            raise ValueError("Partition name cannot be empty")

        # Extracting unit from params, default is 'K'
        self.unit = params.get('unit', 'K').upper()
        if self.unit not in ['B', 'K', 'M']:
            raise ValueError(f"Invalid unit: {self.unit}")

        # Calculate actual size based on unit
        if self.unit == 'B':
            self.actual_size = self.actual_size
        elif self.unit == 'K':
            self.actual_size = self.actual_size * 1024
        elif self.unit == 'M':
            self.actual_size = self.actual_size * 1024 * 1024
        self.type = params.get('type', 'P').upper()
        self.status = 0
        #add the fit parameter too
        self.fit = params.get('fit', 'FF').upper()
        self.byte_inicio = 0
        

    def __str__(self):
        return f"Partition: name={self.name}, size={self.actual_size} bytes,  unit={self.unit}, type={self.type}, status={self.status}, fit={self.fit}, byte_inicio={self.byte_inicio}"

    def pack(self):
        fit_char = self.fit[0].encode() 
        packed_partition = struct.pack(self.FORMAT, self.actual_size, self.name.encode('utf-8'), self.unit.encode('utf-8'), self.type.encode('utf-8'), self.status, fit_char, self.byte_inicio)
        return packed_partition

    @classmethod
    def unpack(cls, data):
        unpacked_data = struct.unpack(cls.FORMAT, data)
        ex = {'size': 10, 'path': 'path', 'name': 'name'}
        partition = cls(ex)
        partition.actual_size = unpacked_data[0]
        partition.name = unpacked_data[1].decode('utf-8').strip('\x00')
        partition.unit = unpacked_data[2].decode('utf-8')
        partition.type = unpacked_data[3].decode('utf-8')
        partition.status = unpacked_data[4]
        fit_char = unpacked_data[5].decode()
        fit_map = {'B': 'BF', 'F': 'FF', 'W': 'WF', 'N': 'NF'}
        partition.fit = fit_map[fit_char]
        partition.byte_inicio = unpacked_data[6]
        
            
        return partition
