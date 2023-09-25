import os
import struct
import time
import random
#JOURNAL
class Journal:
    FORMAT = '1000s'
    SIZE = struct.calcsize(FORMAT)
    
    def __init__(self):
        self.journal_data = '' # Store commands as bytes
    
    def __str__(self) -> str:
        return f"Journal: data={self.journal_data.decode('utf-8')}"
    
    def pack(self):
        packed_journal = struct.pack(self.FORMAT, self.journal_data.encode('utf-8'))
        return packed_journal
    
    @classmethod
    def unpack(cls, data):
        unpacked_data = struct.unpack(cls.FORMAT, data)
        journal = cls()
        journal.journal_data = unpacked_data[0].decode('utf-8').rstrip('\x00')
        return journal


#INODE
class Inode:
    FORMAT = 'i i i d d d c 15i i'
    SIZE = struct.calcsize(FORMAT)

    def __init__(self):
        self.i_uid = 0
        self.I_gid = 0
        self.i_s = 0
        self.i_atime = time.time()
        self.i_ctime = time.time()
        self.i_mtime = time.time()
        self.i_type = '0'
        self.i_block = [-1] * 15
        self.i_perm = 0  # define permissions as required
    def __str__(self) -> str:
        return f"\nInode: uid={self.i_uid},\n gid={self.I_gid},\n size={self.i_s},\n atime={self.i_atime},\n ctime={self.i_ctime},\n mtime={self.i_mtime},\n type={self.i_type},\n block={self.i_block},\n perm={self.i_perm}"
    def pack(self):
        packed_inode = struct.pack(self.FORMAT, self.i_uid, self.I_gid, self.i_s, self.i_atime, self.i_ctime, self.i_mtime, self.i_type.encode('utf-8'), *self.i_block, self.i_perm)
        return packed_inode
    @classmethod
    def unpack(cls, data):
        unpacked_data = struct.unpack(cls.FORMAT, data)
        inode = cls()
        inode.i_uid = unpacked_data[0]
        inode.I_gid = unpacked_data[1]
        inode.i_s = unpacked_data[2]
        inode.i_atime = unpacked_data[3]
        inode.i_ctime = unpacked_data[4]
        inode.i_mtime = unpacked_data[5]
        inode.i_type = unpacked_data[6].decode('utf-8')
        inode.i_block = list(unpacked_data[7:22])
        inode.i_perm = unpacked_data[22]
        return inode
        

#FOLDER BLOCK
class block:
    FORMAT = '64s'
    SIZE = struct.calcsize(FORMAT)

class Content:
    FORMAT = '12s i'
    SIZE = struct.calcsize(FORMAT)

    def __init__(self, name, inode):
        self.b_name = name
        self.b_inodo = inode
    def __str__(self) -> str:
        return f"Name: {self.b_name}\n Inode: {self.b_inodo}"
    def pack(self):
        packed_content = struct.pack(self.FORMAT, self.b_name.encode('utf-8'), self.b_inodo)
        return packed_content
    @classmethod
    def unpack(cls, data):
        unpacked_data = struct.unpack(cls.FORMAT, data)
        content = cls("empty", -1)
        content.b_name = unpacked_data[0].decode('utf-8')
        content.b_inodo = unpacked_data[1]
        return content

class FolderBlock:
    FORMAT = Content.FORMAT * 4
    SIZE = struct.calcsize(FORMAT)

    def __init__(self):
        self.b_content = [Content("empty", -1) for _ in range(4)]
    def __str__(self) -> str:
        text = "FolderBlock: content=["
        for i in range(4):
            text += f"{self.b_content[i]}, "
        text += "]"
        return text
    
    def pack(self):
        packed_objetos = b''.join([obj.pack() for obj in self.b_content])
        return packed_objetos
    @classmethod
    def unpack(cls, data):
        folderblock = cls()
        for i in range(4):
            # Extract the binary data for each Content object
            chunk = data[i * Content.SIZE: (i + 1) * Content.SIZE]
            folderblock.b_content[i] = Content.unpack(chunk)
        return folderblock

class FileBlock:
    FORMAT = '64s'
    SIZE = struct.calcsize(FORMAT)

    def __init__(self):
        self.b_content = "empty"
    def __str__(self) -> str:
        return f"FileBlock: content={self.b_content}"
    def pack(self):
        packed_fileblock = struct.pack(self.FORMAT, self.b_content.encode('utf-8'))
        return packed_fileblock
    @classmethod
    def unpack(cls, data):
        unpacked_data = struct.unpack(cls.FORMAT, data)
        fileblock = cls()
        fileblock.b_content = unpacked_data[0].decode('utf-8')
        return fileblock

class PointerBlock:
    FORMAT = '16i'
    SIZE = struct.calcsize(FORMAT)

    def __init__(self):
        self.b_pointers = [-1] * 16

    
        


class Superblock:
    FORMAT = 'i i i i i d d i i i i i i i i i i'
    SIZE = struct.calcsize(FORMAT)

    def __init__(self, inicio_particion, size_particion,ext):
        if ext == 2:
            number_of_structures = (size_particion - Superblock.SIZE) // (Inode.SIZE + 4+(3*block.SIZE))
        elif ext == 3:
            number_of_structures = (size_particion - Superblock.SIZE) // (Inode.SIZE +Journal.SIZE+ 4+(3*block.SIZE))
        number_of_inodes = number_of_structures //4
        number_of_blocks = number_of_inodes * 3
        self.s_filesystem_type = 0xEF53
        self.s_inodes_count = number_of_inodes
        self.s_blocks_count = number_of_blocks
        self.s_free_blocks_count = number_of_blocks
        self.s_free_inodes_count = number_of_inodes
        self.s_mtime = time.time()  # current time
        self.s_umtime = 0  # not unmounted yet
        self.s_mnt_count = 0  # just mounted
        self.s_magic = 0xEF53
        self.s_inode_s = Inode.SIZE
        self.s_block_s = block.SIZE
        self.s_firts_ino = 0
        self.s_first_blo = 0
        if ext == 2:
            self.s_bm_inode_start = inicio_particion + Superblock.SIZE
        elif ext == 3:
            self.s_bm_inode_start =inicio_particion + Superblock.SIZE + Journal.SIZE
        self.s_bm_block_start = self.s_bm_inode_start + self.s_inodes_count
        self.s_inode_start = self.s_bm_block_start + self.s_blocks_count
        self.s_block_start = self.s_inode_start + (self.s_inodes_count * Inode.SIZE)
    def __str__(self) -> str:
        return f"Superblock: filesystem_type={self.s_filesystem_type}, inodes_count={self.s_inodes_count}, blocks_count={self.s_blocks_count}, free_blocks_count={self.s_free_blocks_count}, free_inodes_count={self.s_free_inodes_count}, mtime={self.s_mtime}, umtime={self.s_umtime}, mnt_count={self.s_mnt_count}, magic={self.s_magic}, inode_s={self.s_inode_s}, block_s={self.s_block_s}, firts_ino={self.s_firts_ino}, first_blo={self.s_first_blo}, bm_inode_start={self.s_bm_inode_start}, bm_block_start={self.s_bm_block_start}, inode_start={self.s_inode_start}, block_start={self.s_block_start}"
    
    def pack(self):
        packed_superblock = struct.pack(self.FORMAT, self.s_filesystem_type, self.s_inodes_count, self.s_blocks_count, self.s_free_blocks_count, self.s_free_inodes_count, self.s_mtime, self.s_umtime, self.s_mnt_count, self.s_magic, self.s_inode_s, self.s_block_s, self.s_firts_ino, self.s_first_blo, self.s_bm_inode_start, self.s_bm_block_start, self.s_inode_start, self.s_block_start)
        return packed_superblock
    def ver_bytes_inidices(self):
        print(f"bm_inode_start={self.s_bm_inode_start}, \nbm_block_start={self.s_bm_block_start},  \ninode_start={self.s_inode_start},  \nblock_start={self.s_block_start} \n count_inodes={self.s_inodes_count} \n count_blocks={self.s_blocks_count}")
        input("____especificaciones de ext y superbloque, presione enter para continuar:::")
    @classmethod
    def unpack(cls, data):
        unpacked_data = struct.unpack(cls.FORMAT, data)
        superblock = cls(0,0,2)
        superblock.s_filesystem_type = unpacked_data[0]
        superblock.s_inodes_count = unpacked_data[1]
        superblock.s_blocks_count = unpacked_data[2]
        superblock.s_free_blocks_count = unpacked_data[3]
        superblock.s_free_inodes_count = unpacked_data[4]
        superblock.s_mtime = unpacked_data[5]
        superblock.s_umtime = unpacked_data[6]
        superblock.s_mnt_count = unpacked_data[7]
        superblock.s_magic = unpacked_data[8]
        superblock.s_inode_s = unpacked_data[9]
        superblock.s_block_s = unpacked_data[10]
        superblock.s_firts_ino = unpacked_data[11]
        superblock.s_first_blo = unpacked_data[12]
        superblock.s_bm_inode_start = unpacked_data[13]
        superblock.s_bm_block_start = unpacked_data[14]
        superblock.s_inode_start = unpacked_data[15]
        superblock.s_block_start = unpacked_data[16]
        return superblock