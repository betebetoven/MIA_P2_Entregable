from FORMATEO.ext2.ext2 import Superblock, Inode, FolderBlock, FileBlock, PointerBlock, block, Content
import os
import struct
import time
import random
from mountingusers import load_users_from_content, parse_users, get_user_if_authenticated, get_id_by_group, extract_active_groups,get_group_id
from FORMATEO.ext2.ext2 import Superblock, Inode, FolderBlock, FileBlock, PointerBlock, block, Content, Journal
import struct
from prettytable import PrettyTable
import re
from mkfile import busca
from mkfs import parse_users
from mountingusers import extract_active_groups, get_group_id

def add_to_journal(mounted_partitions,id, texto):  
    if id == None:
        print("Error: The id is required.")
        return
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break
    if not partition:
        print(f"Error: The partition with id {id} does not exist.")
        return
    # Retrieve partition details.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    filename = path
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return
    with open(full_path, "rb+") as file:
        file.seek(inicio)
        superblock = Superblock.unpack(file.read(Superblock.SIZE))
        try:
            file.seek(inicio+superblock.SIZE)
            journal = Journal.unpack(file.read(Journal.SIZE))
            content = journal.journal_data
            content += texto +  "\n"
            if len(content) > Journal.SIZE:
                #print("Error: The journal is full.")
                #input()
                return
            journal.journal_data = content
            file.seek(inicio+superblock.SIZE)
            file.write(journal.pack())
            #print(f"content of journal: \n{content}")
            #input("presione enter para continuar")
        except:
            print("Error: The journal does not exist., ext2")
            return
            
def ver_journal_actual(mounted_partitions,id):  
    if id == None:
        print("Error: The id is required.")
        return
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break
    if not partition:
        print(f"Error: The partition with id {id} does not exist.")
        return
    # Retrieve partition details.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    filename = path
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return
    with open(full_path, "rb+") as file:
        file.seek(inicio)
        superblock = Superblock.unpack(file.read(Superblock.SIZE))
        try:
            file.seek(inicio+superblock.SIZE)
            journal = Journal.unpack(file.read(Journal.SIZE))
            content = journal.journal_data 
            print(f"content de Journal en {id}: \n{content}")
        except:
            print("Error: The journal does not exist., ext2")
            input("continuar")
            return
#LOSS
def loss(params, mounted_partitions, users):
    print(f'⚰️ <<RUNNING LOSS {params} _ _ _ _ _ _ _ _ _ ')
    id = params.get('id', None)
    # Check if the id exists in mounted_partitions.
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break

    if not partition:
        print(f"Error: The partition with id {id} does not exist.")
        return

    # Retrieve partition details.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    #write null bytes all over the partition
    filename = path
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return
    with open(full_path, "rb+") as file:
        try:
            file.seek(inicio+ Superblock.SIZE)
            minijournal = Journal.unpack(file.read(Journal.SIZE))
        except:
            print("Error: The journal does not exist we are on a ext2")
            return
        file.seek(inicio)
        superblock = Superblock.unpack(file.read(Superblock.SIZE))
        file.seek(superblock.s_bm_inode_start)
        file.write(b'\x00' * superblock.s_inodes_count)
        file.seek(superblock.s_bm_block_start)
        file.write(b'\x00' * superblock.s_blocks_count)
        file.seek(superblock.s_inode_start)
        file.write(b'\x00' * (superblock.s_inodes_count * Inode.SIZE))
        file.seek(superblock.s_block_start)
        file.write(b'\x00' * (superblock.s_blocks_count * 64))
        #get journal
        file.seek(inicio+superblock.SIZE)
        journal = Journal.unpack(file.read(Journal.SIZE))
        print(f"journal_data: \n{journal.journal_data}")