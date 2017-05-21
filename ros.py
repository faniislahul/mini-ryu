from __future__ import print_function
class ros:
    n = int(raw_input())
    if n==0:
        print("PAK CHANEK AMAN")
    elif n<=100:
        s = range(n)
        for i in range(0,n):
            s[i]= raw_input()

        for i in range(0,n):
            words = s[i].split()
            print('KODE@',i+1,'@KATA#PESAN#' , end='')
            for word in words:

                for j in range(len(word)-1,-1,-1):
                    print(word[j], end='')
                print(' ', end='')
            print()
