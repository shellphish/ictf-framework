
class Helper
{
public:
	static void SendMessage(const int fd, const char* strMessage);
	static int RecvMessage(const int fd, unsigned char* pBuffer, int nMaxSize);
	static bool IsStringSanitized(char* pString);
};