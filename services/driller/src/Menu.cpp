#include <string>
#include <sstream>
#include <vector>
#include "Menu.h"
#include "Helper.h"

MenuEntry::MenuEntry(const std::string& strCaption, int (*pHandler)(MenuEntry* pEntry, int nFd))
{
	this->m_pHandler = pHandler;
	this->m_strCaption = strCaption;
}

void MenuEntry::PrintPrompt(int nFd)
{
	Helper::SendMessage(nFd, "======== ");
	Helper::SendMessage(nFd, this->m_strCaption.c_str());
	Helper::SendMessage(nFd, " ========"
		"\n");
	for(int i = 0; i < this->m_vecEntries.size(); ++i)
	{
		std::stringstream ss;
		ss << (i + 1) << ". ";
		Helper::SendMessage(nFd, ss.str().c_str());
		Helper::SendMessage(nFd, this->m_vecEntries[i]->GetCaption().c_str());
		Helper::SendMessage(nFd, "\n");
	}
}

int MenuEntry::Handler(int nFd)
{
	this->PrintPrompt(nFd);
	return this->m_pHandler(this, nFd);
}

std::string MenuEntry::GetCaption()
{
	return this->m_strCaption;
}

void MenuEntry::AddEntry(MenuEntry* pMenuEntry)
{
	this->m_vecEntries.push_back(pMenuEntry);
}

MenuEntry* MenuEntry::GetEntry(int nID)
{
	nID -= 1;
	if(nID < 0 || nID >= this->m_vecEntries.size())
	{
		throw new std::exception();
	}
	return this->m_vecEntries[nID];
}