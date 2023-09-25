comandos = '\
mkdisk -size=10 -path="/home/mis discos/Disco4.dsk" -unit=M -fit=WF \n\
    fdisk -size=150 -path="/home/mis discos/Disco4.dsk" -name=laprimera -type=P\
        fdisk -size=100 -type=E -unit=K -path="/home/mis discos/Disco4.dsk" -name=lasegunda -fit=BF \
            fdisk -size=10 -type=P -unit=K -path="/home/mis discos/Disco4.dsk" -name=latercera -fit=WF \
                fdisk -size=300 -type=P -unit=K -path="/home/mis discos/Disco4.dsk" -name=lacuarta -fit=FF \
                    fdisk -size=10 -type=P -unit=K -path="/home/mis discos/Disco4.dsk" -name=laquinta -fit=BF \
                        fdisk -name=lasegunda -delete=full -path="/home/mis discos/Disco4.dsk" \
                            fdisk -name=lacuarta -delete=full -path="/home/mis discos/Disco4.dsk" \
                            fdisk -size=90 -path="/home/mis discos/Disco4.dsk" -name=laacomodada -fit=WF \
                                fdisk -add=100 -unit=K -path="/home/mis discos/Disco4.dsk" -name=laprimera\
                                    fdisk -size=1 -type=P -unit=K -path="/home/mis discos/Disco4.dsk" -name=laquenoentra -fit=FF \
                                        fdisk -size=1 -type=L -unit=K -path="/home/mis discos/Disco4.dsk" -name=acaandamos -fit=FF \
                                            fdisk -size=1 -type=L -unit=K -path="/home/mis discos/Disco4.dsk" -name=acanosfuimos -fit=FF \
                                                fdisk -size=1 -type=L -unit=K -path="/home/mis discos/Disco4.dsk" -name=acanosreimos -fit=FF \
                                        mount -path="/home/mis discos/Disco4.dsk" -name=laprimera \
    mkfs -type=full -id=531Disco4 -fs=ext2\n\
    logout \
    login -user=root -pass=123 -id=531Disco4\n\
    \
                                                      mkusr -user=user1 -pass=usuario -grp=root\
                                                                          mkgrp -name=usuarios\
                                                                                                 mkgrp -name=usuarios2 \
                                                                                                     mkgrp -name=usuarios3 \
                                                                                                         mkgrp -name=usuarios4 \
                                                                                                             mkgrp -name=usuarios4 \
                                                                                                                 mkusr -user=mamadas -pass=usuario -grp=usuarios4\
                                                      rmgrp -name=usuarios\
                                                          rmusr -user=user1\
                                                              mkfile -path=/users.txt\
                                                                  \
                                                                  mkfile -path=/home/documents/papers/archivos.txt -r -size=10\
                                                                      cat -file1=/users.txt\
                                                                      \
                                                                      mkfile -path=/home/documents/papers/mentos/kk -r \
                                                                          mkfile -path=/home/documents/papers/mentos/kk1 -r \
                                                                              mkfile -path=/home/documents/papers/mentos/kk2 -r \
                                                                                  mkfile -path=/home/documents/papers/mentos/kk3 -r \
                                                                      mkfile -path=/home/documents/papers/mentos/mentos.txt -r -cont=/contenido.txt\
                                                                          mkfile -path=/home2/documents/papers/mentos/mentos2.txt -r -cont=/contenido.txt\
                            remove -path=/home/documents/papers/mentos/mentos.txt\
                                \
                                    \
                                mkfile -path=/home/documents/papers/mentos/mentos.txt -r -cont=/contenido.txt\
                                    mkfile -path=/casa" -r\
                                         mkdir -path=/carro" -r\
                                             rename -path=/carro -name=carrititito\
                                                 edit -path=/home2/documents/papers/mentos/mentos2.txt -cont=/contenido_editado.txt -r\
                                                     mkfile -path=/home2/documents/llena2" -r\
                                                    mkfile -path=/home2/documents/llena3" -r\
                                                        mkfile -path=/home2/documents/llena4" -r\
                                                     copy -path=/home2/documents/papers/mentos/mentos2.txt -destino=/home2/documents\
                                                         move -path=/home2/documents/papers/mentos/mentos2.txt -destino=/home\
                                                             mkfile -path=/home/a.txt" -r\
                                                             find -path="/home" -name=mentos.txt\
                                                                 find -path="/home" -name=mentos2.txt\
find -path="/home" -name=mentos3.txt\n\
pause\n\
find -path="/homes" -name=mentos2.txt   \
find -path="/home" -name=mentos \
pause   \
find -path="/home" -name=?  \
pause   \
find -path="/home" -name=*  \
pause   \
find -path="/home2" -name=* \
chown -path=/home2/documents/mentos2.txt -user=mamadas  \
chown -path=/home2/documents -r -user=mamadas   \
#chgrp -user=mamadas -grp=usuarios2  \
chmod -path=/home2 -ugo=777 -r\n\
    loss -id=531Disco4\
        recovery -id=531Disco4\
                        '                               
#unmount -id=533Disco4 \