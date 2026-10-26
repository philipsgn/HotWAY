import re

def update_page():
    path = 'frontend/src/app/page.tsx'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Update imports
    old_imports = """import ScreenOrders, { Order } from "../components/ScreenOrders";
import ScreenPlanning from "../components/ScreenPlanning";
import ScreenRouteDetail from "../components/ScreenRouteDetail";
import ScreenStrategyLab from "../components/ScreenStrategyLab";
import ScreenSearchReplay from "../components/ScreenSearchReplay";
import ScreenLiveDispatch from "../components/ScreenLiveDispatch";"""

    new_imports = """import ScreenOrders, { Order } from "../components/ScreenOrders";
import ScreenStrategyLab from "../components/ScreenStrategyLab";
import ScreenLiveDispatch from "../components/ScreenLiveDispatch";"""

    text = text.replace(old_imports, new_imports)

    # 2. Update default tab
    text = text.replace('const [activeTab, setActiveTab] = useState<OptimoTab>("orders");', 'const [activeTab, setActiveTab] = useState<OptimoTab>("live");')

    # 3. Update getTabTitle
    pattern_title = r'const getTabTitle = \(tab: OptimoTab\) => \{[\s\S]*?default:[\s\S]*?\}'
    # Actually let's search for getTabTitle
    start_str = "const getTabTitle = (tab: OptimoTab) => {"
    end_str = "    }\n  };"
    start_idx = text.find(start_str)
    if start_idx != -1:
        end_idx = text.find(end_str, start_idx) + len(end_str)
        replacement_title = """const getTabTitle = (tab: OptimoTab) => {
    switch (tab) {
      case "live":
        return "Theo dõi điều phối Semi-MDP";
      case "orders":
        return "Quản lý đơn hàng";
      case "strategy_lab":
        return "Strategy Lab: Đánh giá mô hình";
    }
  };"""
        text = text[:start_idx] + replacement_title + text[end_idx:]

    # 4. Update JSX in FloatingSheet
    start_sheet = "<FloatingSheet"
    start_sheet_idx = text.find(start_sheet)
    if start_sheet_idx != -1:
        end_sheet = "</FloatingSheet>"
        end_sheet_idx = text.find(end_sheet, start_sheet_idx)
        # find the inner part
        sheet_content_start = text.find(">", start_sheet_idx) + 1
        new_sheet_inner = """
        {activeTab === "live" && (
          <ScreenLiveDispatch
            onUpdateMapOrders={(liveOrders) => setOrders(liveOrders)}
            onUpdateSimVehicle={setSimVehicle}
          />
        )}

        {activeTab === "orders" && (
          <ScreenOrders
            orders={orders}
            onLoadSample={handleLoadSample}
            onAddOrder={handleAddOrder}
            onClearOrders={handleClearOrders}
            isLoading={isLoading}
            snapWarnings={snapWarnings}
            selectedOrderId={selectedOrderId}
            onSelectOrder={(id) => setSelectedOrderId(id)}
          />
        )}

        {activeTab === "strategy_lab" && <ScreenStrategyLab />}
      """
        text = text[:sheet_content_start] + new_sheet_inner + text[end_sheet_idx:]

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

    print("frontend/src/app/page.tsx updated successfully!")

if __name__ == "__main__":
    update_page()
