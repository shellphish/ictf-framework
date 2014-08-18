#include <sstream>
#include <iomanip>
#include "User.h"
#include "GlobalState.h"
#include "cryptopp/sha.h"

extern GlobalState* g_pGlobalState;

User::User(const std::string& strAccountName, const std::string& strHashedPassword, bool bIsAdmin, int nID, int nCreatorID)
{
	std::string strAccountNameTrimmed = strAccountName.substr(0, sizeof(this->m_strAccountName) - 1);
	strcpy(this->m_strAccountName, strAccountNameTrimmed.c_str());

	// Dehexify the password string
	unsigned char strCryptedPassword[20];
	for(int i = 0; i < 20; ++i)
	{
		unsigned int nTemp;
		std::stringstream ss;
		ss << std::hex << strHashedPassword.substr(i * 2, 2);
		ss >> nTemp;
		strCryptedPassword[i] = (unsigned char)nTemp;
	}
	memcpy(this->m_strPassword, strCryptedPassword, 20);

	if(bIsAdmin)
	{
		this->m_nIdentity = 1;
	}
	else
	{
		this->m_nIdentity = 0;
	}

	this->m_nCreatorID = nCreatorID;

	this->m_nID = nID;
}

User::User(const std::string& strAccountName, const std::string& strPassword, bool bIsAdmin, int nCreatorID)
{
	std::string strAccountNameTrimmed = strAccountName.substr(0, sizeof(this->m_strAccountName) - 1);
	strcpy(this->m_strAccountName, strAccountNameTrimmed.c_str());

	// Encrypt the password
	unsigned char strCryptedPassword[20];
	// SHA-1 the password
	CryptoPP::SHA().CalculateDigest(strCryptedPassword, (unsigned char*)strPassword.c_str(), strPassword.length());
	memcpy(this->m_strPassword, strCryptedPassword, 20);

	if(bIsAdmin)
	{
		this->m_nIdentity = 1;
	}
	else
	{
		this->m_nIdentity = 0;
	}

	this->m_nCreatorID = nCreatorID;

	// Read the maximum ID from database
	this->m_nID = g_pGlobalState->GetMaxUserID() + 1;
}

char* User::GetName()
{
	return this->m_strAccountName;
}

std::string User::GetPasswordStr()
{
	std::stringstream ss;
	ss << std::hex << std::setfill('0');
	for(int i = 0; i < 20; ++i)
	{
		ss << std::setw(2) << (unsigned int)this->m_strPassword[i];
	}
	return ss.str();
}

bool User::CheckPassword(char* strPassword)
{
	unsigned char strCryptedPassword[20];
	// SHA-1 the password
	CryptoPP::SHA().CalculateDigest(strCryptedPassword, (unsigned char*)strPassword, strlen(strPassword));
	// Compare the password
	for(int i = 0; i < sizeof(this->m_strPassword); ++i)
	{
	
		if(strCryptedPassword[i] == this->m_strPassword[i])
		{
			// Vulnerability here :D
			return true;
		}
	}
	return false;
}

void User::SetPassword(char* strPassword)
{
	unsigned char strCryptedPassword[20];
	// SHA-1 the password
	CryptoPP::SHA().CalculateDigest(strCryptedPassword, (unsigned char*)strPassword, strlen(strPassword));
	memcpy(this->m_strPassword, strCryptedPassword, 20);
}