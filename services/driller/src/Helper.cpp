#include <sys/socket.h>
#include <string.h>
#include <exception>
#include "Helper.h"

void Helper::SendMessage(const int fd, const char* strMessage)
{
	int nLen = strlen(strMessage);
	if(send(fd, strMessage, nLen, 0) != nLen)
	{
		throw new std::exception();
	}
}

int Helper::RecvMessage(const int fd, unsigned char* pBuffer, int nMaxSize)
{
	unsigned char c = 0;
	int nCurrentPos = 0;
	while(nCurrentPos < nMaxSize)
	{
		if(recv(fd, &c, 1, 0) == -1)
		{
			throw new std::exception();
		}
		if(c == '\n')
		{
			break;
		}
		pBuffer[nCurrentPos++] = c;
	}
	return nCurrentPos;
}

bool Helper::IsStringSanitized(char* pString)
{
	char strIllegalChars[] = "\"'/*\t\n\\/`";
	int i = 0;
	while(pString[i] != 0)
	{
		for(int j = 0; j < sizeof(strIllegalChars); ++j)
		{
			if(pString[i] == strIllegalChars[j])
			{
				return false;
			}
		}
		++i;
	}
	return true;
}