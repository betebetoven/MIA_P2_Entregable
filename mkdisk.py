import os
import struct
import time
import random
from MBR import MBR
from EBR import EBR
from PARTICION import Partition
def mkdisk(params):
    print("\n💽 creating disk...")
    # Extract parameters with defaults if not provided
    size = params.get('size')
    filename = params.get('path')
    unit = params.get('unit', 'M')
    fit = params.get('fit', 'FF')

    # Check mandatory parameters
    if not size or not filename:
        print("Both -size and -path parameters are mandatory!")
        return

    # Calculate total size in bytes
    if unit == 'K':
        total_size_bytes = size * 1024
    elif unit == 'M':
        total_size_bytes = size * 1024 * 1024
    else:
        print(f"Invalid unit: {unit}")
        return

    # Check fit value
    if fit not in ['BF', 'FF', 'WF']:
        print(f"Invalid fit value: {fit}")
        return

    current_directory = os.getcwd()
    #print(f"Current directory: {current_directory}")
    full_path= f'{current_directory}/discos_test{filename}'
    #path = os.path.join(current_directory, 'discos_test', filename)
    path = full_path
    #print(f"Full path: {path}")
    # If the directory does not exist, create it
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Create or overwrite the binary file with specified size filled with zeroes
    with open(path, "wb") as file:
        file.write(b'\0' * total_size_bytes)

    print(f"**Disk created successfully at {path} with size {size}{unit}.")
    example = MBR(params)
    with open(path, "rb+") as file:
        file.seek(0)
        file.write(example.pack())
    #print(example)
    #get the full path of the file and print it
    #print(os.path.abspath(path))


def rmdisk(params):
    filename = params.get('path')

    # Check mandatory parameter
    if not filename:
        print("-path parameter is mandatory!")
        return

    # Get the full path to the file
    current_directory = os.getcwd()
    full_path = f'{current_directory}/discos_test{filename}'

    # If the file does not exist, show an error
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return

    # Prompt user for confirmation before deletion
    response = input(f"Are you sure you want to delete {full_path}? (yes/no): ").strip().lower()

    if response == 'yes':
        os.remove(full_path)
        print(f"Disk {full_path} deleted successfully.")
    elif response == 'no':
        print("Disk deletion aborted.")
    else:
        print("Invalid response. Disk not deleted.")

import struct
def fdisk(params):
    print("\n📁 creating partition..."+str(params))
    filename = params.get('path')
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    #check if path exist and if so open the file, if not, return error
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return
    #open the file and read the MBR
    ex = {'size': 10, 'path': 'path', 'name': 'empty'}
    
    nueva_particion = None
    #nueva_particion = Partition(params)
    if 'delete' in params or 'add' in params:
        nueva_particion = Partition(ex)
    else:
        nueva_particion = Partition(params)
    nueva_particion.status = 1
    particion_temporal = nueva_particion
    
    
    #read all 4 partitions
    partitions = []
    with open(full_path, "rb+") as file:
        file.seek(0)
        data = file.read(MBR.SIZE)
        x = MBR.unpack(data[:MBR.SIZE])
        disk_size = x.mbr_tamano
        disk_fit = x.fit
        print("disk size ",disk_size)
        space = disk_size - MBR.SIZE
        
        
        
        for i in range(4):
            file.seek(struct.calcsize(MBR.FORMAT)+(i*Partition.SIZE))
            #unpack the partition
            data = file.read(Partition.SIZE)
            particion_temporal = Partition.unpack(data)
            partitions.append(particion_temporal)
        realizar = True
        if 'delete' in params or 'add' in params:
            realizar = False
        elif all(item.status == 1 for item in partitions) and 'type' in params and nueva_particion.type != 'L':
            realizar = False
            print("No se puede crear la particion, ya que todas las particiones estan ocupadas")
            return
        count_E = sum(1 for item in partitions if item.type == 'E')
        if count_E == 1 and nueva_particion.type == 'E':
            realizar = False
            print("No se puede crear la particion, ya que ya existe una particion extendida")
            return
        
        partitions2 = partitions
        nueva_particion.fit = disk_fit
        byteinicio = MBR.SIZE
        if nueva_particion.type == 'L' and realizar:
            #look for the partition type E in partitions and get the byte_inicio
            for i, item in enumerate(partitions):
                if item.type == 'E':
                    tamano_de_e = item.actual_size
                    inicio_de_e = item.byte_inicio
                    byteinicio = item.byte_inicio
                    limite_final_de_e = item.byte_inicio+item.actual_size
                    file.seek(byteinicio)
                    ebr = EBR.unpack(file.read(EBR.SIZE))
                    if ebr.next == -1:
                        #create the ebr
                        ebr = EBR(params, byteinicio)
                        ebr.next= byteinicio+EBR.SIZE+ebr.actual_size
                        #check if it fits
                        if ebr.next > limite_final_de_e:
                            print("No hay espacio para crear la particion")
                            return
                        file.seek(byteinicio)
                        file.write(ebr.pack())
                        nuevo_ebr = EBR(ex, ebr.next)
                        file.seek(ebr.next)
                        file.write(nuevo_ebr.pack())
                        return
                    else :
                        while ebr.next != -1:
                            file.seek(ebr.next)
                            ebr = EBR.unpack(file.read(EBR.SIZE))
                        #create the ebr
                        nuevo_ebr = EBR(params, ebr.start)
                        nuevo_ebr.next = nuevo_ebr.start+EBR.SIZE+nuevo_ebr.actual_size
                        if nuevo_ebr.next > limite_final_de_e:
                            print("No hay espacio para crear la particion")
                            return
                        file.seek(ebr.start)
                        file.write(nuevo_ebr.pack())
                        nuevo_nuevo_ebr = EBR(ex, nuevo_ebr.next)
                        file.seek(nuevo_ebr.next)
                        file.write(nuevo_nuevo_ebr.pack())
                        return
            print(f'no existe particion extendida, error alagregar la particion logica{params.get("name") }')            
            return
                
            
            
            
            
        
        
        
        if nueva_particion.fit == 'FF' and realizar:
            nueva_particion.fit = params.get('fit', 'FF').upper()
            for i, item in enumerate(partitions):   
                if (item.status == 0 and item.name == "empty") or (item.status ==0 and space >= nueva_particion.actual_size):   
                    if i == 0:
                        byteinicio = MBR.SIZE
                    else :
                        byteinicio = partitions[i-1].byte_inicio+partitions[i-1].actual_size
                    probable = byteinicio+nueva_particion.actual_size
                    permiso = True
                    for j, item2 in enumerate(partitions2[(i+1):]):
                        if probable > item2.byte_inicio and item2.byte_inicio != 0:
                            permiso = False
                        
                    if permiso == True:        
                        nueva_particion.byte_inicio = byteinicio
                        partitions[i] = nueva_particion
                        item = nueva_particion
                        print(f"Partition {partitions[i]} created successfully.")
                        break 
            packed_objetos = b''.join([obj.pack() for obj in partitions])
            file.seek(struct.calcsize(MBR.FORMAT))
            file.write(packed_objetos)
            if nueva_particion.type == 'E':
                #create the ebr
                ebr = EBR(ex, nueva_particion.byte_inicio)
                file.seek(nueva_particion.byte_inicio)
                file.write(ebr.pack())
            
            return 
        elif nueva_particion.fit == 'BF' and realizar:
            nueva_particion.fit = params.get('fit', 'FF').upper()
            sale = space+1
            indice = -1
            for i,n in enumerate(partitions):
                #print("i ",i)
                if (n.status == 0 and n.name == "empty") and (i==0 or partitions[i-1].status == 1):
                    if i == 0:
                        anterior = MBR.SIZE
                    else :
                        anterior = partitions[i-1].byte_inicio+partitions[i-1].actual_size
                        
                    siguiente = -1    
                    
                    
                    if i == 3 and n.status == 0:
                        siguiente = disk_size
                    for j, n2 in enumerate(partitions2[(i+1):]):
                        #print("j ",j)
                        if n2.status == 1:
                            siguiente = n2.byte_inicio
                            break
                        elif j ==len(partitions2[(i+1):])-1 and n2.status == 0:
                            siguiente = disk_size
                            
                    print("siguiente ",siguiente)
                    print("anterior ",anterior)
                    print("actual size ",nueva_particion.actual_size)
                    print("sale ",sale)
                    espacio = siguiente-anterior
                    print("espacio ",espacio)
                    print(nueva_particion.actual_size <= espacio and espacio < sale)
                    
                    
                    if nueva_particion.actual_size <= espacio and espacio < sale:
                        sale = espacio
                        print("--------sale ",sale)
                        indice = i
                        print("---------indice ",indice)
                        byteinicio = anterior
                        print("---------byteinicio ",byteinicio)
                
            nueva_particion.byte_inicio = byteinicio
            partitions[indice] = nueva_particion
            #print len size of partitions
            print("partitions size ",len(partitions))
            
            print(f"se escribio la particion en el indice {indice}")
            packed_objetos = b''.join([obj.pack() for obj in partitions])
            file.seek(struct.calcsize(MBR.FORMAT))
            file.write(packed_objetos)
            if nueva_particion.type == 'E':
                #create the ebr
                ebr = EBR(ex, nueva_particion.byte_inicio)
                file.seek(nueva_particion.byte_inicio)
                file.write(ebr.pack())
            return
        elif nueva_particion.fit == 'WF' and realizar:
            nueva_particion.fit = params.get('fit', 'FF').upper()
            max_space = -1  # Start with a negative value as a sentinel.
            indice = -1
            for i, n in enumerate(partitions):
                print("i ", i)
                if (n.status == 0 and n.name == "empty") and (i == 0 or partitions[i - 1].status == 1):
                    if i == 0:
                        anterior = MBR.SIZE
                    else:
                        anterior = partitions[i - 1].byte_inicio + partitions[i - 1].actual_size

                    siguiente = -1

                    if i == 3 and n.status == 0:
                        siguiente = disk_size
                    for j, n2 in enumerate(partitions2[(i + 1):]):
                        print("j ", j)
                        if n2.status == 1:
                            siguiente = n2.byte_inicio
                            break
                        elif j == len(partitions2[(i + 1):]) - 1 and n2.status == 0:
                            siguiente = disk_size

                    print("siguiente ", siguiente)
                    print("anterior ", anterior)
                    print("actual size ", nueva_particion.actual_size)
                    espacio = siguiente - anterior
                    print("espacio ", espacio)

                    if nueva_particion.actual_size <= espacio and espacio > max_space:
                        max_space = espacio
                        print("--------max_space ", max_space)
                        indice = i
                        print("---------indice ", indice)
                        byteinicio = anterior
                        print("---------byteinicio ", byteinicio)

            if indice != -1:
                nueva_particion.byte_inicio = byteinicio
                partitions[indice] = nueva_particion
                print("partitions size ", len(partitions))
                print(f"se escribio la particion en el indice {indice}")
                packed_objetos = b''.join([obj.pack() for obj in partitions])
                file.seek(struct.calcsize(MBR.FORMAT))
                file.write(packed_objetos)
                if nueva_particion.type == 'E':
                    #create the ebr
                    ebr = EBR(ex, nueva_particion.byte_inicio)
                    #ebr.name = "aquideberiaestarescritoelnombredelebr"
                    file.seek(nueva_particion.byte_inicio)
                    file.write(ebr.pack())
                return
            else:
                print("No available space for the partition using WF algorithm.")
        elif 'delete' in params:
            partition_name_to_delete = params.get('name')
            if not partition_name_to_delete:
                print("Error: No partition name provided for deletion.")
                return
            partition_found = False
            for i, partition in enumerate(partitions):
                if partition.name == partition_name_to_delete:
                    # Confirm deletion
                    user_input = input(f"Are you sure you want to delete the partition named {partition_name_to_delete}? (yes/no): ")
                    if user_input.lower() != "yes":
                        print("Deletion aborted by the user.")
                        return

                    partition_found = True
                    # Update the partition details
                    partition.status = 0
                    partition.name = "empty"
                    partition.type = "P"

                    # If it's a 'full' delete, fill the partition space with \0 character
                    #start_byte = partition.byte_inicio
                    #end_byte = start_byte + partition.actual_size
                    #file.seek(start_byte)
                    #file.write(b'\0' * (end_byte - start_byte))

                    # Update the partition table in the file
                    packed_objetos = b''.join([obj.pack() for obj in partitions])
                    file.seek(struct.calcsize(MBR.FORMAT))
                    file.write(packed_objetos)
                    print(f"Partition {partition_name_to_delete} has been deleted successfully.")
                    return

            if not partition_found:
                print(f"Error: Partition {partition_name_to_delete} not found.")
                return
        elif 'add' in params:
            # Get the name of the partition to resize
            partition_name_to_resize = params.get('name')
            if not partition_name_to_resize:
                print("Error: No partition name provided for resizing.")
                return

            # Get the size to add to the partition
            try:
                additional_size = int(params['add'])
                unit = params.get('unit', 'K').upper()  # default to Kilobytes if not provided
                if unit == 'B':
                    multiplier = 1
                elif unit == 'K':
                    multiplier = 1024
                elif unit == 'M':
                    multiplier = 1024 * 1024
                
                additional_size = additional_size * multiplier
            except ValueError:
                print("Error: Invalid value for additional size.")
                return

            partition_found = False
            for i, partition in enumerate(partitions):
                if partition.name == partition_name_to_resize:
                    partition_found = True
                    
                    # Calculate the space after the current partition
                    if i == len(partitions) - 1:  # if it's the last partition
                        free_space = disk_size - (partition.byte_inicio + partition.actual_size)
                    else:
                        for j,m in enumerate(partitions2[(i + 1):]):
                            if m.status == 1:
                                free_space = m.byte_inicio - (partition.byte_inicio + partition.actual_size)
                                break
                            elif j == len(partitions2[(i + 1):]) - 1 and m.status == 0:
                                free_space = disk_size - (partition.byte_inicio + partition.actual_size)
                                break
                        
                        
                        #free_space = partitions[i+1].byte_inicio - (partition.byte_inicio + partition.actual_size)

                    # Check if we have enough space to add the additional_size
                    if additional_size <= free_space:
                        # Update the partition's size
                        partition.actual_size += additional_size
                        
                        if partition.actual_size <= 0:
                            print("⚠️  Error: particion de tamaño negativo")
                            return
                        # Update the partition table in the file
                        packed_objetos = b''.join([obj.pack() for obj in partitions])
                        file.seek(struct.calcsize(MBR.FORMAT))
                        file.write(packed_objetos)
                        print(str(partition))
                        print(f"✅  Partition {partition_name_to_resize} has been resized successfully.")
                        
                    else:
                        print(f"⚠️  Error: Not enough space to extend the partition {partition_name_to_resize}.")
                    return

            if not partition_found:
                print(f"Error: Partition {partition_name_to_resize} not found.")
                return

                    
              
    #le mandamos el pack     
    
    
     
            
    
    
    