import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Users, QrCode, Plus, Star, TrendingUp, ArrowUpRight, ArrowDownRight, ChevronDown, ChevronUp, RotateCcw, ChevronRight } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { MobileLayout } from "@/components/MobileLayout";
import { MigrationOverlay } from "@/components/MigrationOverlay";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from "@/components/ui/collapsible";

export default function DashboardPage() {
    const { user, api } = useAuth();
    const navigate = useNavigate();
    const [stats, setStats] = useState(null);
    const [recentCustomers, setRecentCustomers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [sortBy, setSortBy] = useState("recent");
    const [quickActionsOpen, setQuickActionsOpen] = useState(false);
    const [showMigrationOverlay, setShowMigrationOverlay] = useState(false);
    const [migrationChecked, setMigrationChecked] = useState(false);

    const fetchCustomers = async (sort) => {
        try {
            let endpoint = "/customers?limit=5";
            if (sort === "most_visited") {
                endpoint = "/customers?limit=5&sort_by=total_visits&sort_order=desc";
            } else if (sort === "most_spent") {
                endpoint = "/customers?limit=5&sort_by=total_spent&sort_order=desc";
            } else if (sort === "highest_points") {
                endpoint = "/customers?limit=5&sort_by=total_points&sort_order=desc";
            }
            const res = await api.get(endpoint);
            setRecentCustomers(res.data);
        } catch (err) {
            console.error("Failed to fetch customers", err);
        }
    };

    // Check migration status on first load
    useEffect(() => {
        const checkMigrationStatus = async () => {
            try {
                const res = await api.get("/migration/status");
                // Show overlay if migration not confirmed and not skipped permanently
                if (!res.data.migration_confirmed && !res.data.migration_skipped_permanently) {
                    setShowMigrationOverlay(true);
                }
            } catch (err) {
                console.error("Failed to check migration status", err);
            } finally {
                setMigrationChecked(true);
            }
        };
        checkMigrationStatus();
    }, []);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, customersRes] = await Promise.all([
                    api.get("/analytics/dashboard"),
                    api.get("/customers?limit=5")
                ]);
                setStats(statsRes.data);
                setRecentCustomers(customersRes.data);
            } catch (err) {
                toast.error("Failed to load dashboard");
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    useEffect(() => {
        if (!loading) {
            fetchCustomers(sortBy);
        }
    }, [sortBy]);

    if (loading) {
        return (
            <MobileLayout>
                <div className="p-4 animate-pulse">
                    <div className="h-8 bg-gray-200 rounded w-48 mb-4"></div>
                    <div className="grid grid-cols-3 gap-2 mb-3">
                        <div className="h-20 bg-gray-200 rounded-xl"></div>
                        <div className="h-20 bg-gray-200 rounded-xl"></div>
                        <div className="h-20 bg-gray-200 rounded-xl"></div>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                        <div className="h-20 bg-gray-200 rounded-xl"></div>
                        <div className="h-20 bg-gray-200 rounded-xl"></div>
                        <div className="h-20 bg-gray-200 rounded-xl"></div>
                    </div>
                </div>
            </MobileLayout>
        );
    }

    return (
        <MobileLayout>
            {/* Migration Overlay */}
            {showMigrationOverlay && (
                <MigrationOverlay 
                    api={api}
                    onClose={() => setShowMigrationOverlay(false)}
                    onComplete={() => setShowMigrationOverlay(false)}
                />
            )}
            
            <div className="p-4 max-w-lg mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-5">
                    <div>
                        <p className="text-[#52525B] text-sm font-body">Welcome</p>
                        <h1 className="text-2xl font-bold text-[#2B2B2B] font-heading" data-testid="restaurant-name">
                            {user?.restaurant_name}
                        </h1>
                    </div>
                    <Avatar className="w-10 h-10 bg-[#F26B33]">
                        <AvatarFallback className="bg-[#F26B33] text-white font-semibold">
                            {user?.restaurant_name?.charAt(0)}
                        </AvatarFallback>
                    </Avatar>
                </div>

                {/* Stats Grid - 3 columns */}
                {/* Row 1: Customers, Active, Avg Visits */}
                <div className="grid grid-cols-3 gap-2 mb-2">
                    <div className="stats-card-compact" data-testid="total-customers-card">
                        <div className="flex items-center gap-1 text-[#F26B33] mb-1">
                            <Users className="w-3.5 h-3.5" />
                            <span className="text-[10px] font-medium uppercase tracking-wider font-body">Customers</span>
                        </div>
                        <p className="text-xl font-bold text-[#2B2B2B] font-heading">
                            {stats?.total_customers || 0}
                        </p>
                        <p className="text-[10px] text-[#52525B] flex items-center gap-0.5 font-body">
                            <TrendingUp className="w-3 h-3" />
                            +{stats?.new_customers_7d || 0} this week
                        </p>
                    </div>
                    <div className="stats-card-compact" data-testid="active-customers-card">
                        <div className="flex items-center gap-1 text-[#F26B33] mb-1">
                            <Users className="w-3.5 h-3.5" />
                            <span className="text-[10px] font-medium uppercase tracking-wider font-body">Active(30d)</span>
                        </div>
                        <p className="text-xl font-bold text-[#2B2B2B] font-heading">
                            {stats?.active_customers_30d || 0}
                        </p>
                    </div>
                    <div className="stats-card-compact" data-testid="avg-visits-card">
                        <div className="flex items-center gap-1 text-[#F26B33] mb-1">
                            <RotateCcw className="w-3.5 h-3.5" />
                            <span className="text-[10px] font-medium uppercase tracking-wider font-body">Avg Visits</span>
                        </div>
                        <p className="text-xl font-bold text-[#2B2B2B] font-heading">
                            {stats?.avg_visits_per_customer || 0}
                        </p>
                    </div>
                </div>

                {/* Row 2: Points Issued, Points Redeemed, Rating */}
                <div className="grid grid-cols-3 gap-2 mb-5">
                    <div className="stats-card-compact" data-testid="points-issued-card">
                        <div className="flex items-center gap-1 text-[#329937] mb-1">
                            <ArrowUpRight className="w-3.5 h-3.5" />
                            <span className="text-[10px] font-medium uppercase tracking-wider font-body">Points Issued</span>
                        </div>
                        <p className="text-xl font-bold text-[#2B2B2B] font-heading points-display">
                            {stats?.total_points_issued?.toLocaleString() || 0}
                        </p>
                    </div>
                    <div className="stats-card-compact" data-testid="points-redeemed-card">
                        <div className="flex items-center gap-1 text-[#329937] mb-1">
                            <ArrowDownRight className="w-3.5 h-3.5" />
                            <span className="text-[10px] font-medium uppercase tracking-wider font-body">Redeemed</span>
                        </div>
                        <p className="text-xl font-bold text-[#2B2B2B] font-heading points-display">
                            {stats?.total_points_redeemed?.toLocaleString() || 0}
                        </p>
                    </div>
                    <div className="stats-card-compact" data-testid="avg-rating-card">
                        <div className="flex items-center gap-1 text-[#329937] mb-1">
                            <Star className="w-3.5 h-3.5 fill-current" />
                            <span className="text-[10px] font-medium uppercase tracking-wider font-body">Rating</span>
                        </div>
                        <p className="text-xl font-bold text-[#2B2B2B] font-heading">
                            {stats?.avg_rating || "N/A"}
                        </p>
                    </div>
                </div>

                {/* Quick Actions - Hidden for now
                <Collapsible open={quickActionsOpen} onOpenChange={setQuickActionsOpen} className="mb-5">
                    <CollapsibleTrigger asChild>
                        <button className="flex items-center justify-between w-full text-left py-2 px-1">
                            <h2 className="text-sm font-semibold text-[#52525B] font-['Montserrat']">Quick Actions</h2>
                            {quickActionsOpen ? (
                                <ChevronUp className="w-4 h-4 text-[#52525B]" />
                            ) : (
                                <ChevronDown className="w-4 h-4 text-[#52525B]" />
                            )}
                        </button>
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                        <div className="grid grid-cols-2 gap-3 pt-2">
                            <button 
                                onClick={() => navigate("/customers", { state: { openAddModal: true }})}
                                className="quick-action-btn-compact"
                                data-testid="quick-add-customer"
                            >
                                <div className="w-9 h-9 rounded-full bg-[#F26B33]/10 flex items-center justify-center mr-3">
                                    <Plus className="w-4 h-4 text-[#F26B33]" />
                                </div>
                                <span className="text-sm font-medium text-[#1A1A1A]">Add Customer</span>
                            </button>
                            <button 
                                onClick={() => navigate("/qr")}
                                className="quick-action-btn-compact"
                                data-testid="quick-qr-code"
                            >
                                <div className="w-9 h-9 rounded-full bg-[#329937]/10 flex items-center justify-center mr-3">
                                    <QrCode className="w-4 h-4 text-[#329937]" />
                                </div>
                                <span className="text-sm font-medium text-[#1A1A1A]">Show QR</span>
                            </button>
                        </div>
                    </CollapsibleContent>
                </Collapsible>
                */}

                {/* Recent Customers */}
                <div className="flex items-center justify-between mb-3">
                    <h2 className="text-base font-semibold text-[#2B2B2B] font-heading">Recent Customers</h2>
                    <div className="flex items-center gap-2">
                        <Select value={sortBy} onValueChange={setSortBy}>
                            <SelectTrigger className="h-8 text-xs w-[120px] border-gray-200 font-body" data-testid="sort-dropdown">
                                <SelectValue placeholder="Sort by" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="recent">Recent</SelectItem>
                                <SelectItem value="most_visited">Most Visited</SelectItem>
                                <SelectItem value="most_spent">Most Spent</SelectItem>
                                <SelectItem value="highest_points">Highest Points</SelectItem>
                            </SelectContent>
                        </Select>
                        <button 
                            onClick={() => navigate("/customers")}
                            className="text-xs text-[#F26B33] font-medium whitespace-nowrap font-body hover:text-[#D85A2A]"
                            data-testid="view-all-customers"
                        >
                            View all
                        </button>
                    </div>
                </div>

                {recentCustomers.length === 0 ? (
                    <div className="empty-state">
                        <Users className="empty-state-icon" />
                        <p className="text-[#52525B]">No customers yet</p>
                        <Button 
                            onClick={() => navigate("/customers", { state: { openAddModal: true }})}
                            className="mt-4 bg-[#F26B33] hover:bg-[#D85A2A] rounded-full"
                            data-testid="add-first-customer"
                        >
                            Add your first customer
                        </Button>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {recentCustomers.map((customer) => {
                            // Format total_spent as ₹23K or ₹1.2L
                            const formatSpent = (amount) => {
                                if (!amount || amount === 0) return '₹0';
                                if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`;
                                if (amount >= 1000) return `₹${(amount / 1000).toFixed(0)}K`;
                                return `₹${amount}`;
                            };
                            
                            // Format last visit as relative time
                            const formatLastVisit = (dateStr) => {
                                if (!dateStr) return 'Never';
                                const date = new Date(dateStr);
                                const now = new Date();
                                const diffMs = now - date;
                                const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
                                
                                if (diffDays === 0) return 'Today';
                                if (diffDays === 1) return '1d ago';
                                if (diffDays < 7) return `${diffDays}d ago`;
                                if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
                                if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`;
                                return `${Math.floor(diffDays / 365)}y ago`;
                            };
                            
                            const customerName = customer.name && customer.name.trim() ? customer.name : "Unknown";
                            
                            return (
                                <button
                                    key={customer.id}
                                    onClick={() => navigate(`/customers/${customer.id}`)}
                                    className="customer-list-item w-full text-left"
                                    data-testid={`customer-item-${customer.id}`}
                                >
                                    <Avatar className="w-10 h-10 mr-3">
                                        <AvatarFallback className="bg-[#329937]/10 text-[#329937] font-semibold font-body">
                                            {customerName.charAt(0)}
                                        </AvatarFallback>
                                    </Avatar>
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-[#2B2B2B] truncate font-body">{customerName}</p>
                                        <p className="text-sm text-[#52525B] font-body">
                                            {customer.total_visits || 0} visits · {formatSpent(customer.total_spent)} · {formatLastVisit(customer.last_visit)}
                                        </p>
                                    </div>
                                    <div className="text-right flex items-center gap-3">
                                        {customer.wallet_balance > 0 && (
                                            <div className="text-right border-r pr-3 border-gray-200">
                                                <p className="font-semibold text-[#F26B33]">₹{customer.wallet_balance.toLocaleString()}</p>
                                                <p className="text-[10px] text-[#A1A1AA] font-body">Wallet</p>
                                            </div>
                                        )}
                                        <div className="text-right">
                                            <p className="font-semibold text-[#329937] points-display text-sm">{customer.total_points} pts</p>
                                            <Badge variant="outline" className={`tier-badge ${customer.tier.toLowerCase()}`}>
                                                {customer.tier}
                                            </Badge>
                                        </div>
                                        <ChevronRight className="w-5 h-5 text-[#A1A1AA]" />
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                )}
            </div>
        </MobileLayout>
    );
}
