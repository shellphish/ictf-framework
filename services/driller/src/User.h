#include <string>

class User
{
public:
	User(const std::string& strAccountName, const std::string& strHashedPassword, bool bIsAdmin, int nID, int nCreatorID);
	User(const std::string& strAccountName, const std::string& strPassword, bool bIsAdmin, int nCreatorID);
	char* GetName();
	int GetID() { return m_nID; }
	int GetCreatorID() { return m_nCreatorID; }
	std::string GetPasswordStr();
	void SetAdmin(bool bIsAdmin) { m_nIdentity = bIsAdmin? 1: 0; }
	bool IsAdmin() { return !(m_nIdentity == 0); }
	bool CheckPassword(char* strPassword);
	void SetPassword(char* strPassword);
private:
	int m_nID; /* 4 bytes */
	int m_nCreatorID; /* 4 bytes */
	int m_nIdentity; /* 4 bytes */
					 /* Logic: 0 if is not an admin, otherwise for admin -- Vulnerability ;) */
	char m_strAccountName[40];
	unsigned char m_strPassword[20]; /* SHA-1'ed password */
};