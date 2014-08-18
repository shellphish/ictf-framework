import os
import re
import random

LabelCounter = 0

def obfuscate(assembly):
	global LabelCounter

	# Eliminate all calls
	new_asm = ""
	last_end = 0
	for match in re.finditer(r'call\t([\S]+)\n', assembly):
		if match.group(1)[0 : 1] != "*":
			# Generate a label for GetPc
			getpc_label = ".getpc_%d" % LabelCounter
			# Increment the global counter
			LabelCounter += 1
			new_asm += assembly[last_end : match.start()]
			getpc_method_index = random.randint(0, 2)
			if getpc_method_index == 0:
				# call-pop-add
				new_asm += "" + \
					"call	" + getpc_label + "\n" + \
					getpc_label + ":\n" + \
					"pushl	%eax\n" + \
					"movl	4(%esp), %eax\n" + \
					"addl	$19, %eax\n" + \
					"movl	%eax, 4(%esp)\n" + \
					"popl	%eax\n" + \
					"push	$" + match.group(1) + "\n" + \
					"ret\n"
			elif getpc_method_index == 1:
				# call-mov-add_esp-add
				new_asm += "" + \
					"call	" + getpc_label + "\n" + \
					getpc_label + ":\n" + \
					"movl	%eax, -4(%esp)\n" + \
					"movl	(%esp), %eax\n" + \
					"addl	$4, %esp\n" + \
					"addl	$24, %eax\n" + \
					"pushl	%eax\n" + \
					"movl	-4(%esp), %eax\n" + \
					"push	$" + match.group(1) + "\n" + \
					"ret\n"
			elif getpc_method_index == 2:
				# call-mov-add_esp-add
				new_asm += "" + \
					"call	" + getpc_label + "\n" + \
					getpc_label + ":\n" + \
					"movl	%eax, -4(%esp)\n" + \
					"movl	(%esp), %eax\n" + \
					"addl	$4, %esp\n" + \
					"addl	$23, %eax\n" + \
					"pushl	%eax\n" + \
					"movl	-4(%esp), %eax\n" + \
					"jmp	" + match.group(1) + "\n"
			last_end = match.end()
	assembly = new_asm + assembly[last_end : ]

	# Replace prolog and epilog
	new_asm = ""
	last_end = 0
	for match in re.finditer(r'\.cfi_startproc\n((\t\.cfi[^\n]+\n){0,2})\tpushl\t%ebp', assembly):
		prefix_stuff = ""
		if len(match.group(1)) > 0:
			prefix_stuff = match.group(1)
		new_asm += assembly[last_end : match.start()]
		# Generate a label for GetPc
		jmp_label = ".jmp_%d" % LabelCounter
		# Increment the global counter
		LabelCounter += 1
		new_asm += ".cfi_startproc\n" + \
					prefix_stuff + \
					"pushl	%eax\n" + \
					"xor	%eax, %eax\n" + \
					"jz	" + jmp_label + "\n" + \
					".byte	0x0f\n" + \
					jmp_label + ":\n" + \
					"popl	%eax\n" + \
					"pushl	%ebp\n"
		last_end = match.end()
	assembly = new_asm + assembly[last_end : ]

	
	new_asm = ""
	last_end = 0
	for match in re.finditer(r'ret\n\t\.cfi_endproc\n', assembly):
		new_asm += assembly[last_end : match.start()]
		new_asm +=	"popl	%edx\n" + \
					"jmp 	*%edx\n" + \
					".byte	0x65\n.byte	0x6e\n.byte	0x64\n.byte	0x20\n.byte 0x70\n.byte 0x72\n.byte 0x6f\n.byte 0x63\n" + \
					".cfi_endproc\n"
		last_end = match.end()
	assembly = new_asm + assembly[last_end : ]


	# IDA-fucker!
	# This is already an IDA-fucker... unintentional :P

	return assembly

def main():
	file_list = os.listdir(".")
	for filename in file_list:
		if filename[len(filename) - 2 : ] == ".s":
			print "[+]Asm file %s found." % filename
			f = open(filename, "r")
			asm = f.read()
			f.close()
			asm = obfuscate(asm)
			f = open(filename, "w")
			f.write(asm)
			f.close()
			print "[+]%s processed." % filename

if __name__ == "__main__":
	main()