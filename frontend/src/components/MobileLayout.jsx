import { useNavigate, useLocation } from "react-router-dom";
import { Home, Users, FileText, MessageSquare, Settings } from "lucide-react";
import { DemoModeBanner } from "@/components/shared/DemoModeBanner";

export const MobileLayout = ({ children }) => {
    const navigate = useNavigate();
    const location = useLocation();
    
    const navItems = [
        { path: "/", icon: Home, label: "Home" },
        { path: "/customers", icon: Users, label: "Customers" },
        { path: "/templates", icon: FileText, label: "Templates" },
        { path: "/feedback", icon: MessageSquare, label: "Feedback" },
        { path: "/settings", icon: Settings, label: "Settings" }
    ];

    return (
        <div className="min-h-screen bg-[#F9F9F7] pb-20">
            <DemoModeBanner />
            {children}
            
            {/* Bottom Navigation */}
            <nav className="mobile-bottom-nav bottom-nav" data-testid="bottom-nav">
                <div className="flex items-center justify-around h-16 max-w-lg mx-auto">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        const Icon = item.icon;
                        return (
                            <button
                                key={item.path}
                                onClick={() => navigate(item.path)}
                                className={`mobile-bottom-nav-item ${isActive ? "active" : ""}`}
                                data-testid={`nav-${item.label.toLowerCase()}`}
                            >
                                <Icon className="w-5 h-5" strokeWidth={1.5} />
                                <span>{item.label}</span>
                            </button>
                        );
                    })}
                </div>
            </nav>
        </div>
    );
};
