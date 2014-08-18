#include <string>

class Driller
{
public:
	Driller(const std::string& strName, const std::string& strLocation, int nID, int nDepth, int nSpotID);
	Driller(const std::string& strName, const std::string& strLocation, int nDepth, int nSpotID);
	std::string GetName() { return m_strName; }
	std::string GetLocation() { return m_strLocation; }
	int GetID() { return m_nID; }
	int GetDepth() { return m_nDepth; }
	int GetSpotID() { return m_nSpotID; }
	void Drill(int nDepth);
private:
	int m_nID;
	int m_nDepth;	/* Maximum 0xffffffff */
	int m_nSpotID;
    std::string m_strName;
    std::string m_strLocation;
};
