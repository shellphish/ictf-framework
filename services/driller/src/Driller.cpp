#include "Driller.h"
#include "GlobalState.h"

extern GlobalState* g_pGlobalState;

Driller::Driller(const std::string& strName, const std::string& strLocation, int nID, int nDepth, int nSpotID)
{
    this->m_strName = strName;
    this->m_strLocation = strLocation;
    this->m_nID = nID;
    this->m_nDepth = 0;
    this->m_nSpotID = nSpotID;
}

Driller::Driller(const std::string& strName, const std::string& strLocation, int nDepth, int nSpotID)
{
	this->m_strName = strName;
    this->m_strLocation = strLocation;
    this->m_nID = g_pGlobalState->GetMaxDrillerID() + 1;
    this->m_nDepth = 0;
    this->m_nSpotID = nSpotID;
}

void Driller::Drill(int nDepth)
{
    this->m_nDepth += nDepth;
}
