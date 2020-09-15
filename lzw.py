import argparse
import array
import sys

if (sys.version_info[0] != 3):
    print("You must use Python 3 -- Exiting")
    sys.exit()

from bitstring import BitString

class LZW():

    def __init__(self, word_size=16):
        self.word_size = word_size

    def encode(self, message):

        output = []
        main_dictionary = {}
        for i in range(256):
            main_dictionary[chr(i)]=i
        string = message[0]
        curr_index = 0
        l = len(message)
        while curr_index<l-1:
            symbol = message[curr_index+1]
            if string+symbol in main_dictionary:
                string+=symbol
            else:
                output.append(main_dictionary[string])
                max_key = max(main_dictionary,key = main_dictionary.get)
                max_val = main_dictionary[max_key]
                if max_val==2**16-1:
                    main_dictionary = {}
                    for i in range(256):
                        main_dictionary[chr(i)]=i
                    #main_dictionary[string+symbol]=0
                else:
                    main_dictionary[string+symbol]=max_val+1
                string = symbol
            curr_index+=1
        output.append(main_dictionary[string])
        bits = BitString()
        bits.pack_numbers(output,16)
        return bits

    def decode(self, bits):
        # TODO: Your code here

        # You will need to change this return statement to return a meaningful string
        numbers = bits.unpack_all_numbers(16)
        output_string = ''
        decode_dict = {}
        for i in range(256):
            decode_dict[i]=chr(i)
        string = decode_dict[numbers[0]]
        curr_index = 0
        output_string+=string
        l = len(numbers)
        while curr_index<l-1 :
            code = numbers[curr_index+1]
            if code not in decode_dict:
                entry = string + string[0]
            else:
                entry = decode_dict[code]
            output_string+=entry
            max_key = max(list(decode_dict.keys()))
            decode_dict[max_key+1]= string+entry[0]
            string = entry
            curr_index+=1
        return output_string


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', type=str, help='filename to compress or decompress', required=True)
    parser.add_argument('-d', '--decompress', help='decompress file', action='store_true')
    args = parser.parse_args()

    lzw = LZW()

    if not args.decompress:
        # read in the file
        f = open(args.filename, 'rb')
        compressed = [chr(k) for k in array.array("B", f.read())]
        f.close()
        # encode and output
        x = lzw.encode(compressed)
        new_filename = args.filename + '.encoded'
        x.write_to_file(new_filename)
        print("Saved encoded file as %s" % new_filename)

    else:
        b = BitString()
        b.read_in_file(args.filename)
        x = lzw.decode(b)
        new_filename = args.filename + '.decoded'
        with open(new_filename, "w") as f:
            f.write(x)
        print("Saved decoded file as %s" % new_filename)
