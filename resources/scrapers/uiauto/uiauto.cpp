/* uiauto.cpp: allows to scrape the window under focus
 * using Microsong UI Automation APIs.
 *
 * Requirements:
 *
 *  - Windows Vista or greater
 *  - rapidjson: https://github.com/Tencent/rapidjson
 *
 * Usage:
 *
 *  uiauto.exe [recursive] [minimize-console]
 *
 *    - recursive:
 *        if true, it will scan recursively the content of the window
 *        yielding more information but taking longer
 *    - minimize-console:
 *        to be used from a prompt to manually run the scraper.
 *        If true, minimize the console and scrape the first available window.
 */

#include <string>
#include <iomanip>
#include <sstream>
#include <iostream>

#include <stdio.h>
#include <tchar.h>
#include <atlbase.h>
#include <uiautomation.h>

#include "rapidjson/writer.h"
#include "rapidjson/document.h"
#include "rapidjson/encodings.h"
#include "rapidjson/stringbuffer.h"

#if !RAPIDJSON_HAS_STDSTRING
#define RAPIDJSON_HAS_STDSTRING 1
#endif

void list_children(IUIAutomation *, IUIAutomationTreeWalker *,
                   IUIAutomationElement *, rapidjson::Document &,
                   rapidjson::Value &, bool);
HRESULT initialize_uiautomation(IUIAutomation **);
std::wstring get_name(IUIAutomationElement *);
RECT get_window(IUIAutomation *, IUIAutomationElement *);
RECT get_frame(IUIAutomationElement *);
bool get_toggle_state(IUIAutomationElement *);
bool get_clickable_state(IUIAutomationElement *);
void json_add_text(rapidjson::Document &, rapidjson::Value &,
                   const std::wstring &);
void json_add_coordinates(rapidjson::Document &, rapidjson::Value &,
                          const char*, RECT);
void json_add_element(rapidjson::Document &, rapidjson::Value &,
                      IUIAutomation *, IUIAutomationElement *);
void check_hresult(HRESULT);
std::string utf16_to_utf8(const std::wstring &);

int scrape(HWND hwnd, bool recursive)
{
    CComPtr<IUIAutomation> uiauto;

    if (initialize_uiautomation(&uiauto) != S_OK) {
        std::cerr << "Failed initializing UIAutomation, exit..." << std::endl;
        return -1;
    }

    rapidjson::Document json;
    json.SetObject();

    CComPtr<IUIAutomationElement> element;

    try {
        check_hresult(uiauto->ElementFromHandle(hwnd, &element));
        json_add_element(json, json, uiauto, element);

        CComPtr<IUIAutomationTreeWalker> walker;
        rapidjson::Value children(rapidjson::Type::kArrayType);

        check_hresult(uiauto->get_ControlViewWalker(&walker));
        list_children(uiauto, walker, element, json, children, recursive);
        json.AddMember("children", children, json.GetAllocator());
    } catch (int error) {
        std::cerr << "Failed to get foreground window... " << std::to_string(
            (long double) error) << std::endl;
    }

    rapidjson::GenericStringBuffer<rapidjson::ASCII<>> buffer;
    rapidjson::Writer<
        rapidjson::GenericStringBuffer<rapidjson::ASCII<>>> writer(buffer);

    json.Accept(writer);

    std::cout << buffer.GetString() << std::endl;

    return 0;
}

void list_children(IUIAutomation *uiauto, IUIAutomationTreeWalker *walker,
                   IUIAutomationElement *parent, rapidjson::Document &json,
                   rapidjson::Value &children, bool recursive)
{
    BOOL enabled;
    IUIAutomationElement *node = NULL;

    walker->GetFirstChildElement(parent, &node);
    if (node == NULL)
        return;

    while (node)
	{
            CONTROLTYPEID control_type;
            IUIAutomationElement *next;
            HRESULT hres = node->get_CurrentControlType(&control_type);

            enabled = false;

            if (hres == S_OK)
                hres = node->get_CurrentIsEnabled(&enabled);

            if (hres == S_OK && enabled == TRUE) {
                rapidjson::Value object(rapidjson::Type::kObjectType);

                json_add_element(json, object, uiauto, node);

                if (recursive) {
                    rapidjson::Value childs(rapidjson::Type::kArrayType);

                    list_children(
                        uiauto, walker, node, json, childs, recursive);
                    object.AddMember("children", childs, json.GetAllocator());
                }

                children.PushBack(object, json.GetAllocator());
            }

            walker->GetNextSiblingElement(node, &next);
            node->Release();
            node = next;
	}

    if (node != NULL)
        node->Release();

    return;
}

HRESULT initialize_uiautomation(IUIAutomation **ppAutomation)
{
    return CoCreateInstance(
        CLSID_CUIAutomation, NULL, CLSCTX_INPROC_SERVER,
        IID_IUIAutomation, reinterpret_cast<void**>(ppAutomation));
}

std::wstring get_name(IUIAutomationElement *element)
{
    BSTR bstring;
    std::wstring ret;

    check_hresult(element->get_CurrentName(&bstring));
    ret.append(bstring, SysStringLen(bstring));
    SysFreeString(bstring);

    return ret;
}

RECT get_window(IUIAutomation *uiauto, IUIAutomationElement *element)
{
    RECT rect;
    VARIANT vrect;

    check_hresult(element->GetCurrentPropertyValue(
                      UIA_BoundingRectanglePropertyId, &vrect));
    check_hresult(uiauto->VariantToRect(vrect, &rect));

    VariantClear(&vrect);

    return rect;
}

RECT get_frame(IUIAutomationElement *element)
{
    RECT frame;
    VARIANT vhwnd;

    check_hresult(element->GetCurrentPropertyValue(
                      UIA_NativeWindowHandlePropertyId, &vhwnd));
    GetClientRect(reinterpret_cast<HWND>(vhwnd.lVal), &frame);

    VariantClear(&vhwnd);

    return frame;
}

bool get_toggle_state(IUIAutomationElement *element)
{
    HRESULT hres;
    VARIANT vstate;
    bool state = false;

    hres = element->GetCurrentPropertyValue(
        UIA_ToggleToggleStatePropertyId, &vstate);
    if (hres == S_OK)
        state = (ToggleState) vstate.lVal == ToggleState_On ? true : false;

    VariantClear(&vstate);

    return state;
}

bool get_focus_state(IUIAutomationElement *element)
{
    HRESULT hres;
    VARIANT vstate;
    bool state = false;

    hres = element->GetCurrentPropertyValue(
        UIA_HasKeyboardFocusPropertyId, &vstate);
    if (hres == S_OK)
        state = (bool) vstate.boolVal;

    VariantClear(&vstate);

    return state;
}

bool get_clickable_state(IUIAutomationElement *element)
{
    VARIANT vstate;

    check_hresult(element->GetCurrentPropertyValue(
                      UIA_ClickablePointPropertyId, &vstate));

    VariantClear(&vstate);

    return vstate.vt == VT_EMPTY;
}

void json_add_text(rapidjson::Document& json, rapidjson::Value& value,
                   const std::wstring& text)
{
    rapidjson::Value temp;

    temp.SetString(utf16_to_utf8(text).c_str(), json.GetAllocator());
    value.AddMember("text", temp, json.GetAllocator());
}

void json_add_coordinates(rapidjson::Document &json, rapidjson::Value &value,
                          const char *label, RECT rect)
{
    rapidjson::Value array;
    rapidjson::Value key(label, json.GetAllocator());

    array.SetArray();
    array.PushBack(rapidjson::Value((int)rect.left), json.GetAllocator());
    array.PushBack(rapidjson::Value((int)rect.top), json.GetAllocator());
    array.PushBack(rapidjson::Value((int)rect.right), json.GetAllocator());
    array.PushBack(rapidjson::Value((int)rect.bottom), json.GetAllocator());

    value.AddMember(key, array, json.GetAllocator());
}

void json_add_properties(rapidjson::Document &json, rapidjson::Value &value,
                         IUIAutomationElement *element)
{
    value.AddMember("toggled", get_toggle_state(element), json.GetAllocator());
    value.AddMember("focused", get_focus_state(element), json.GetAllocator());
    value.AddMember(
        "clickable", get_clickable_state(element), json.GetAllocator());
}

void json_add_element(rapidjson::Document &json, rapidjson::Value &value,
                      IUIAutomation *uiauto, IUIAutomationElement *element)
{
    CONTROLTYPEID control_type = 0;
    HRESULT hr = element->get_CurrentControlType(&control_type);

    json_add_text(json, value, get_name(element));
    json_add_coordinates(
        json, value, "coordinates", get_window(uiauto, element));
    json_add_properties(json, value, element);

    /* If the value is the window, add its frame coordinates. */
    if (json == value)
        json_add_coordinates(
            json, value, "frame_coordinates", get_frame(element));

    value.AddMember("type", control_type, json.GetAllocator());
}

std::string utf16_to_utf8(const std::wstring &str)
{
    int len;
    std::string ret;

    len = WideCharToMultiByte(
        CP_UTF8, 0, str.c_str(), str.length(), NULL, 0, NULL, NULL);
    if (len > 0) {
        ret.resize(len);
        WideCharToMultiByte(CP_UTF8, 0, str.c_str(), str.length(),
                            const_cast<char*>(ret.c_str()), len, NULL, NULL);
    }

    return ret;
}

void check_hresult(HRESULT hres)
{
    if (hres != S_OK)
        throw hres;
}

int _tmain(int argc, _TCHAR *argv[])
{
    int ret;
    HWND hwnd, hconsolewnd;
    bool console, recursive;

    recursive = (argc > 1 && !_tcscmp(argv[1], _T("true"))) ? true : false;
    console = (argc > 2 && !_tcscmp(argv[2], _T("true"))) ? true : false;

    /* Minimize Console Window if requested */
    hconsolewnd = GetConsoleWindow();
    if (console) {
        ShowWindow(hconsolewnd, SW_MINIMIZE);

        Sleep(2000);
    }

    hwnd = GetForegroundWindow();

    if (CoInitialize(NULL) != S_OK) {
        std::cerr << "Failed CoInitialize, exit..." << std::endl;
        return -1;
    }

    ret = scrape(hwnd, recursive);

    CoUninitialize();

    if (console)
        ShowWindow(hconsolewnd, SW_RESTORE);

    return ret;
}
