import sys

from collections import defaultdict
from bitstring import BitString

if (sys.version_info[0] != 3):
    print("You must use Python 3 -- Exiting")
    sys.exit()

class HuffmanTree:

    def __init__(self, source):
        # self.source is a dictionary mapping symbols to
        # probabilities.  E.g., {"A" : .1, "B" : .9}
        self.source = source

        # You should *not* complete this lab by editing self.source --
        # consider it a read-only data structure.  If you want to add
        # your own data structure(s) in __init__, feel free

        # Build the tree and the codebook
        self.root = None
        self.build_tree()
        self.codebook = None
        self.set_codebook()

    # build_tree() does not return anything.  At the end of a call to
    # build_tree(), self.root should be set to point to a HuffmanNode
    # representing the root of a Huffman tree corresponding to the
    # symbols and probabilities given in self.source
    def build_tree(self):

        # TODO: Your code here.  You're also free to add additional
        # data structures in __init__, if you wish.

        # At the end, self.root should be set to a HuffmanNode that
        # represents the root of the Huffman tree.
        #
        # self.root = 
        # At first, for all symbols in source, we create a huffman node.
        # we will keep removing the nodes with two smallest probabilities and a node with probability equal
        # to their sum and keep doing it until we have only one node which will be the root
        # Thoughts on ds, for efficiency we can take a sorted list of probabilities 
        node_dict = {}
        for element in self.source:
            node = HuffmanNode(element,self.source[element])
            node_dict[node]=self.source[element]
        while len(node_dict)>1:
            min1 = min(node_dict, key= node_dict.get)
            del node_dict[min1]
            min2 = min(node_dict, key= node_dict.get)
            del node_dict[min2]
            new_prob = min1.probability+min2.probability
            new_node = HuffmanNode(symbol=None,probability = new_prob)
            new_node.left_child = min1
            new_node.right_child = min2 
            node_dict[new_node] = new_prob
        root_node = min(node_dict,key=node_dict.get)
        self.root = root_node

    # encode() returns a string of 0's and 1's representing the binary
    # encoding of message.
    def encode(self, message):
        s = ""
        try:
            s = "".join([self.codebook[m] for m in message])
        except:
            print("Error in encoding the message ", message)
            print("Codebook: ", self.codebook)
        return s

    # Creates the codebook for this tree, which maps symbols to binary
    # strings.  HuffmanNode.walk() does the real work here.
    def set_codebook(self):
        self.codebook = self.root.walk()
                

class HuffmanNode:

    # Instead of having separate classes for internal and leaf nodes,
    # we have a single class -- HuffmanNode.  For internal nodes, the
    # left and right children should both be defined.  For the leaf
    # nodes, the left and right children should be set to None.
    #
    # Conceptually, it doesn't make sense to have a symbol associated
    # with internal nodes.  It's fine to set self.symbol to None in
    # those cases, or really, whatever you want; we will only read 
    # self.symbol for leaf nodes.
    #
    # self.probability should reflect the probability associated with
    # that node.  For leaf nodes, that's the probability of the
    # corresponding symbol.  For internal nodes, it's the probability
    # of the symbols in the subtree.
    #
    # You are welcome to add additional variables if you need them.
    def __init__(self, symbol, probability):
        self.left_child = None
        self.right_child = None
        self.probability = probability
        self.symbol = symbol

    # This code walks the tree rooted at self, assigning 0's to left
    # edges and 1's to right edges.
    #
    # This code is more robust than is necessary -- it will do its
    # best to encode even invalid trees (those that aren't
    # prefix-free, or that have some internal nodes with only one
    # child).  For instance:
    #
    # *         results in the following encoding:
    #  \         A = 1
    #   A        B = 11
    #    \
    #     B
    #
    #     *     results in the following encoding:
    #    / \     A = 00
    #   *   B    B = 1
    #  /
    # A
    def walk(self, current_bitstring=""):

        # Degenerate case -- a single node.
        if (current_bitstring == "" and self.left_child is None and self.right_child is None):
            return {self.symbol : "0"}

        # Start with the symbol at this node.  Note that this code
        # will print symbols for internal nodes that have symbols
        # associated with them.  In proper Huffman encoding, there
        # should be no such nodes.
        book = {}
        if self.symbol is not None:
            book[self.symbol] = current_bitstring

        # Walk down any defined children
        book_left = {}
        book_right = {}
        if self.left_child is not None:
            book_left = self.left_child.walk(current_bitstring + "0")
        if self.right_child is not None:
            book_right = self.right_child.walk(current_bitstring + "1")

        # Merge the resulting dictionaries.  This code would be
        # simpler were it not also trying to detect whether any symbol
        # is repeated (which can happen in the case of internal nodes
        # having symbols assigned).
        for k in book_left:
            if k in book:
                print("Warning -- symbol %s appears multiple times in your tree.  Are you setting the symbols of internal nodes to None?" % k)
        book.update(book_left)
        for k in book_right:
            if k in book:
                print("Warning -- symbol %s appears multiple times in your tree.  Are you setting the symbols of internal nodes to None?" % k)
        book.update(book_right)

        return book

    # "less than" method, for sorting trees
    def __lt__(self, other):
        return self.probability < other.probability
