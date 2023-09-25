import os
import struct
import time
import random
from MBR import MBR
from PARTICION import Partition
def mount(params, mounted_partitions):
    print(f'👆<<RUNNING MOUNT {params}_ _ _ _ _ _ _ _ _ ')
    filename = params.get('path')
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return
    partitions = []
    with open(full_path, "rb+") as file:
        for i in range(4):
            file.seek(struct.calcsize(MBR.FORMAT)+(i*Partition.SIZE))
            data = file.read(Partition.SIZE)
            particion_temporal = Partition.unpack(data)
            partitions.append(particion_temporal)

    name = params.get('name')
    bandera = False
    index = -50
    for i,item in enumerate(partitions):
        if item.name == name:
            bandera = True
            index = i
    if bandera == False:
        print(f"Error: The partition {name} does not exist.")
        return
    mycarne = 53
    diskname = filename.split('/')[-1]
    diskname = diskname.split('.')[0]
    #id is defined *Últimos dos dígitos del Carnet + Número Partición + NombreDisco Ejemplo:por ejemplo para el carnet -> 201404106 Id´s -> 061Disco1, 062Disco1, 061Disco2, 062Disco2
    id = f'{mycarne}{(len(mounted_partitions)+1)}{diskname}'
    # append the new dictionary to the list
    mounted_partitions.append({id: {'path':filename , 
                                    'partition': partitions[index],
                                    'name': name,
                                    'index': index,
                                    'id': id,
                                    'inicio': partitions[index].byte_inicio,
                                    'size': partitions[index].actual_size,}})
    print(f"Partition {name} was mounted successfully as {id}.")
#make unmount, it will receive params and you have to get id, and then delete the dictionary with that id from the list
def unmount(params, mounted_partitions):
    print(f'👇<<RUNNING UN-MOUNT {params}_ _ _ _ _ _ _ _ _ ')
    id_to_unmount = params.get('id')
    
    for index, partition_dict in enumerate(mounted_partitions):
        if id_to_unmount in partition_dict:
            mounted_partitions.pop(index)
            print(f"Partition {id_to_unmount} was unmounted successfully.")
            return
        else:  # This gets executed if the loop wasn't broken by the break statement.
            print(f"Error: The partition {id_to_unmount} does not exist.")

