import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { toast } from "sonner";
import { 
    Users, Plus, Search, ChevronRight, Star, TrendingUp, Gift, Phone, User, Check,
    Edit2, Trash2, Building2, Calendar, MapPin, Filter, Clock, ChevronDown, Tag,
    ChevronLeft, Save, Layers, Wallet, Rocket, Cake, Heart, Utensils, MessageCircle,
    Flag, Crown, Leaf, ChevronUp, Home, Sparkles
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { MobileLayout } from "@/components/MobileLayout";
import { ComingSoonOverlay } from "@/components/shared/ComingSoonOverlay";
import { COUNTRY_CODES, GENDER_OPTIONS, LANGUAGE_OPTIONS } from "@/lib/constants";

export default function CustomersPage() {
    const { api, isDemoMode } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [customers, setCustomers] = useState([]);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [syncing, setSyncing] = useState(false);
    const [showAddModal, setShowAddModal] = useState(location.state?.openAddModal || false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [editingCustomer, setEditingCustomer] = useState(null);
    const [showFilters, setShowFilters] = useState(false);
    const [segments, setSegments] = useState(null);
    const [filters, setFilters] = useState({
        tier: "all",
        customer_type: "all",
        last_visit_days: "all",
        city: "",
        sort_by: "created_at",
        sort_order: "desc",
        // New filters
        whatsapp_opt_in: "all",
        vip_flag: "all",
        diet_preference: "all",
        lead_source: "all",
        preferred_time_slot: "all",
        preferred_dining_type: "all",
        has_birthday_this_month: false,
        has_anniversary_this_month: false,
        total_visits: "all",
        blacklist_flag: "all",
        complaint_flag: "all"
    });
    const [expandedFilterGroups, setExpandedFilterGroups] = useState(["basic"]);
    const [newCustomer, setNewCustomer] = useState({ 
        // Basic Information
        name: "", 
        phone: "", 
        country_code: "+91",
        email: "", 
        gender: "",
        dob: "",
        anniversary: "",
        preferred_language: "",
        customer_type: "normal",
        segment_tags: [],
        
        // Contact & Marketing Permissions
        whatsapp_opt_in: false,
        promo_whatsapp_allowed: true,
        promo_sms_allowed: true,
        email_marketing_allowed: true,
        call_allowed: true,
        is_blocked: false,
        
        // Loyalty Information
        referral_code: "",
        referred_by: "",
        membership_id: "",
        membership_expiry: "",
        
        // Behavior & Preferences
        favorite_category: "",
        preferred_payment_mode: "",
        
        // Customer Source & Journey
        lead_source: "",
        campaign_source: "",
        assigned_salesperson: "",
        
        // WhatsApp CRM Tracking
        last_whatsapp_sent: "",
        last_whatsapp_response: "",
        last_campaign_clicked: "",
        last_coupon_used: "",
        automation_status_tag: "",
        
        // Corporate Information
        gst_name: "",
        gst_number: "",
        billing_address: "",
        credit_limit: "",
        payment_terms: "",
        
        // Address
        address: "",
        address_line_2: "",
        city: "",
        state: "",
        pincode: "",
        country: "",
        delivery_instructions: "",
        map_location: null,
        
        // Preferences
        allergies: [],
        favorites: [],
        
        // Dining Preferences
        preferred_dining_type: "",
        preferred_time_slot: "",
        favorite_table: "",
        avg_party_size: "",
        diet_preference: "",
        spice_level: "",
        cuisine_preference: "",
        
        // Special Occasions
        kids_birthday: [],
        spouse_name: "",
        festival_preference: [],
        special_dates: [],
        
        // Feedback & Flags
        last_rating: "",
        nps_score: "",
        complaint_flag: false,
        vip_flag: false,
        blacklist_flag: false,
        
        // AI/Advanced
        predicted_next_visit: "",
        churn_risk_score: "",
        recommended_offer_type: "",
        price_sensitivity_score: "",
        
        // Custom Fields
        custom_field_1: "",
        custom_field_2: "",
        custom_field_3: "",
        
        // Notes
        notes: ""
    });
    const [editData, setEditData] = useState({});
    const [submitting, setSubmitting] = useState(false);
    const [showSaveSegmentDialog, setShowSaveSegmentDialog] = useState(false);
    const [segmentName, setSegmentName] = useState("");
    const [savedSegments, setSavedSegments] = useState([]);
    const [selectedSegment, setSelectedSegment] = useState(null);
    const [customerTab, setCustomerTab] = useState("customers"); // "customers" or "segments"

    const buildQueryString = () => {
        const params = new URLSearchParams();
        if (search) params.append("search", search);
        if (filters.tier && filters.tier !== "all") params.append("tier", filters.tier);
        if (filters.customer_type && filters.customer_type !== "all") params.append("customer_type", filters.customer_type);
        if (filters.last_visit_days && filters.last_visit_days !== "all") params.append("last_visit_days", filters.last_visit_days);
        if (filters.city) params.append("city", filters.city);
        if (filters.sort_by) params.append("sort_by", filters.sort_by);
        if (filters.sort_order) params.append("sort_order", filters.sort_order);
        // New filter params
        if (filters.whatsapp_opt_in && filters.whatsapp_opt_in !== "all") params.append("whatsapp_opt_in", filters.whatsapp_opt_in);
        if (filters.vip_flag && filters.vip_flag !== "all") params.append("vip_flag", filters.vip_flag);
        if (filters.diet_preference && filters.diet_preference !== "all") params.append("diet_preference", filters.diet_preference);
        if (filters.lead_source && filters.lead_source !== "all") params.append("lead_source", filters.lead_source);
        if (filters.preferred_time_slot && filters.preferred_time_slot !== "all") params.append("preferred_time_slot", filters.preferred_time_slot);
        if (filters.preferred_dining_type && filters.preferred_dining_type !== "all") params.append("preferred_dining_type", filters.preferred_dining_type);
        if (filters.has_birthday_this_month) params.append("has_birthday_this_month", "true");
        if (filters.has_anniversary_this_month) params.append("has_anniversary_this_month", "true");
        if (filters.total_visits && filters.total_visits !== "all") params.append("total_visits", filters.total_visits);
        if (filters.blacklist_flag && filters.blacklist_flag !== "all") params.append("blacklist_flag", filters.blacklist_flag);
        if (filters.complaint_flag && filters.complaint_flag !== "all") params.append("complaint_flag", filters.complaint_flag);
        return params.toString();
    };

    const fetchCustomers = async () => {
        try {
            const queryString = buildQueryString();
            const res = await api.get(`/customers${queryString ? `?${queryString}` : ""}`);
            setCustomers(res.data);
        } catch (err) {
            toast.error("Failed to load customers");
        } finally {
            setLoading(false);
        }
    };

    const syncFromMyGenie = async () => {
        setSyncing(true);
        try {
            const res = await api.post("/customers/sync-from-mygenie");
            toast.success(res.data.message || "Customers synced successfully!");
            await fetchCustomers(); // Refresh the list
        } catch (err) {
            toast.error(err.response?.data?.detail || "Failed to sync customers from MyGenie");
        } finally {
            setSyncing(false);
        }
    };

    const saveAsSegment = async () => {
        if (!segmentName.trim()) {
            toast.error("Please enter a segment name");
            return;
        }

        try {
            const segmentFilters = {
                tier: filters.tier !== "all" ? filters.tier : undefined,
                customer_type: filters.customer_type !== "all" ? filters.customer_type : undefined,
                last_visit_days: filters.last_visit_days !== "all" ? filters.last_visit_days : undefined,
                city: filters.city || undefined,
                search: search || undefined
            };

            // Remove undefined values
            Object.keys(segmentFilters).forEach(key => 
                segmentFilters[key] === undefined && delete segmentFilters[key]
            );

            await api.post('/segments', {
                name: segmentName,
                filters: segmentFilters
            });

            toast.success(`Segment "${segmentName}" saved successfully!`);
            setShowSaveSegmentDialog(false);
            setSegmentName("");
            fetchSegments();
        } catch (err) {
            toast.error("Failed to save segment");
        }
    };

    const loadSegment = async (segment) => {
        setSelectedSegment(segment);
        const segmentFilters = segment.filters;
        
        setFilters({
            tier: segmentFilters.tier || "all",
            customer_type: segmentFilters.customer_type || "all",
            last_visit_days: segmentFilters.last_visit_days || "all",
            city: segmentFilters.city || "",
            sort_by: "created_at",
            sort_order: "desc"
        });
        setSearch(segmentFilters.search || "");
    };

    const deleteSegment = async (segmentId) => {
        if (!window.confirm("Are you sure you want to delete this segment?")) return;
        
        try {
            await api.delete(`/segments/${segmentId}`);
            toast.success("Segment deleted");
            fetchSegments();
            if (selectedSegment?.id === segmentId) {
                setSelectedSegment(null);
            }
        } catch (err) {
            toast.error("Failed to delete segment");
        }
    };

    const fetchSegments = async () => {
        try {
            // Fetch segment stats for analytics
            const statsRes = await api.get("/customers/segments/stats");
            setSegments(statsRes.data);
            
            // Fetch saved segments for filtering
            const segmentsRes = await api.get('/segments');
            setSavedSegments(segmentsRes.data);
        } catch (err) {
            console.error("Failed to load segments:", err);
        }
    };

    useEffect(() => {
        fetchCustomers();
        fetchSegments();
    }, [search, filters]);

    const handleAddCustomer = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            const customerData = {
                name: newCustomer.name,
                phone: newCustomer.phone,
                country_code: newCustomer.country_code,
                email: newCustomer.email || null,
                gender: newCustomer.gender || null,
                dob: newCustomer.dob || null,
                anniversary: newCustomer.anniversary || null,
                preferred_language: newCustomer.preferred_language || null,
                customer_type: newCustomer.customer_type,
            };
            await api.post("/customers", customerData);
            toast.success("Customer added!");
            setShowAddModal(false);
            resetForm();
            fetchCustomers();
            fetchSegments();
        } catch (err) {
            toast.error(err.response?.data?.detail || "Failed to add customer");
        } finally {
            setSubmitting(false);
        }
    };

    const resetForm = () => {
        setNewCustomer({ 
            // Basic Information
            name: "", phone: "", country_code: "+91", email: "",
            gender: "", dob: "", anniversary: "", preferred_language: "",
            customer_type: "normal", segment_tags: [],
            // Contact & Marketing Permissions
            whatsapp_opt_in: false, promo_whatsapp_allowed: true,
            promo_sms_allowed: true, email_marketing_allowed: true,
            call_allowed: true, is_blocked: false,
            // Loyalty Information
            referral_code: "", referred_by: "", membership_id: "", membership_expiry: "",
            // Behavior & Preferences
            favorite_category: "", preferred_payment_mode: "",
            // Customer Source & Journey
            lead_source: "", campaign_source: "", assigned_salesperson: "",
            // WhatsApp CRM Tracking
            last_whatsapp_sent: "", last_whatsapp_response: "", last_campaign_clicked: "",
            last_coupon_used: "", automation_status_tag: "",
            // Corporate Information
            gst_name: "", gst_number: "", billing_address: "", credit_limit: "", payment_terms: "",
            // Address
            address: "", address_line_2: "", city: "", state: "", pincode: "", country: "",
            delivery_instructions: "", map_location: null,
            // Preferences
            allergies: [], favorites: [],
            // Dining Preferences
            preferred_dining_type: "", preferred_time_slot: "", favorite_table: "",
            avg_party_size: "", diet_preference: "", spice_level: "", cuisine_preference: "",
            // Special Occasions
            kids_birthday: [], spouse_name: "", festival_preference: [], special_dates: [],
            // Feedback & Flags
            last_rating: "", nps_score: "", complaint_flag: false, vip_flag: false, blacklist_flag: false,
            // AI/Advanced
            predicted_next_visit: "", churn_risk_score: "", recommended_offer_type: "", price_sensitivity_score: "",
            // Custom Fields
            custom_field_1: "", custom_field_2: "", custom_field_3: "",
            // Notes
            notes: ""
        });
    };

    const clearFilters = () => {
        setFilters({
            tier: "all",
            customer_type: "all",
            last_visit_days: "all",
            city: "",
            sort_by: "created_at",
            sort_order: "desc",
            whatsapp_opt_in: "all",
            vip_flag: "all",
            diet_preference: "all",
            lead_source: "all",
            preferred_time_slot: "all",
            preferred_dining_type: "all",
            has_birthday_this_month: false,
            has_anniversary_this_month: false,
            total_visits: "all",
            blacklist_flag: "all",
            complaint_flag: "all"
        });
    };

    const activeFiltersCount = [
        filters.tier !== "all" ? 1 : 0,
        filters.customer_type !== "all" ? 1 : 0,
        filters.last_visit_days !== "all" ? 1 : 0,
        filters.city ? 1 : 0,
        filters.whatsapp_opt_in !== "all" ? 1 : 0,
        filters.vip_flag !== "all" ? 1 : 0,
        filters.diet_preference !== "all" ? 1 : 0,
        filters.lead_source !== "all" ? 1 : 0,
        filters.preferred_time_slot !== "all" ? 1 : 0,
        filters.preferred_dining_type !== "all" ? 1 : 0,
        filters.has_birthday_this_month ? 1 : 0,
        filters.has_anniversary_this_month ? 1 : 0,
        filters.total_visits !== "all" ? 1 : 0,
        filters.blacklist_flag !== "all" ? 1 : 0,
        filters.complaint_flag !== "all" ? 1 : 0
    ].reduce((a, b) => a + b, 0);

    const toggleFilterGroup = (group) => {
        setExpandedFilterGroups(prev => 
            prev.includes(group) 
                ? prev.filter(g => g !== group)
                : [...prev, group]
        );
    };

    const openEditModal = (customer, e) => {
        e.stopPropagation(); // Prevent navigation to detail page
        setEditingCustomer(customer);
        setEditData({
            // Basic Information
            name: customer.name,
            phone: customer.phone,
            country_code: customer.country_code || "+91",
            email: customer.email || "",
            gender: customer.gender || "",
            dob: customer.dob || "",
            anniversary: customer.anniversary || "",
            preferred_language: customer.preferred_language || "",
            customer_type: customer.customer_type || "normal",
            segment_tags: customer.segment_tags || [],
            // Contact & Marketing Permissions
            whatsapp_opt_in: customer.whatsapp_opt_in || false,
            promo_whatsapp_allowed: customer.promo_whatsapp_allowed !== false,
            promo_sms_allowed: customer.promo_sms_allowed !== false,
            email_marketing_allowed: customer.email_marketing_allowed !== false,
            call_allowed: customer.call_allowed !== false,
            is_blocked: customer.is_blocked || false,
            // Loyalty Information
            referral_code: customer.referral_code || "",
            referred_by: customer.referred_by || "",
            membership_id: customer.membership_id || "",
            membership_expiry: customer.membership_expiry || "",
            // Behavior & Preferences
            favorite_category: customer.favorite_category || "",
            preferred_payment_mode: customer.preferred_payment_mode || "",
            // Customer Source & Journey
            lead_source: customer.lead_source || "",
            campaign_source: customer.campaign_source || "",
            last_interaction_date: customer.last_interaction_date || "",
            assigned_salesperson: customer.assigned_salesperson || "",
            // WhatsApp CRM Tracking
            last_whatsapp_sent: customer.last_whatsapp_sent || "",
            last_whatsapp_response: customer.last_whatsapp_response || "",
            last_campaign_clicked: customer.last_campaign_clicked || "",
            last_coupon_used: customer.last_coupon_used || "",
            automation_status_tag: customer.automation_status_tag || "",
            // Corporate Information
            gst_name: customer.gst_name || "",
            gst_number: customer.gst_number || "",
            billing_address: customer.billing_address || "",
            credit_limit: customer.credit_limit || "",
            payment_terms: customer.payment_terms || "",
            // Address
            address: customer.address || "",
            address_line_2: customer.address_line_2 || "",
            city: customer.city || "",
            state: customer.state || "",
            pincode: customer.pincode || "",
            country: customer.country || "",
            delivery_instructions: customer.delivery_instructions || "",
            map_location: customer.map_location || null,
            // Preferences
            allergies: customer.allergies || [],
            favorites: customer.favorites || [],
            // Dining Preferences
            preferred_dining_type: customer.preferred_dining_type || "",
            preferred_time_slot: customer.preferred_time_slot || "",
            favorite_table: customer.favorite_table || "",
            avg_party_size: customer.avg_party_size || "",
            diet_preference: customer.diet_preference || "",
            spice_level: customer.spice_level || "",
            cuisine_preference: customer.cuisine_preference || "",
            // Special Occasions
            kids_birthday: customer.kids_birthday || [],
            spouse_name: customer.spouse_name || "",
            festival_preference: customer.festival_preference || [],
            special_dates: customer.special_dates || [],
            // Feedback & Flags
            last_rating: customer.last_rating || "",
            nps_score: customer.nps_score || "",
            complaint_flag: customer.complaint_flag || false,
            vip_flag: customer.vip_flag || false,
            blacklist_flag: customer.blacklist_flag || false,
            // AI/Advanced
            predicted_next_visit: customer.predicted_next_visit || "",
            churn_risk_score: customer.churn_risk_score || "",
            recommended_offer_type: customer.recommended_offer_type || "",
            price_sensitivity_score: customer.price_sensitivity_score || "",
            // Custom Fields
            custom_field_1: customer.custom_field_1 || "",
            custom_field_2: customer.custom_field_2 || "",
            custom_field_3: customer.custom_field_3 || "",
            // Notes
            notes: customer.notes || ""
        });
        setShowEditModal(true);
    };

    const handleUpdateCustomer = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            // Only send fields that have actual values to avoid overwriting with empty strings
            const cleanData = {};
            for (const [key, value] of Object.entries(editData)) {
                if (value !== "" && value !== null && value !== undefined) {
                    cleanData[key] = value;
                }
            }
            await api.put(`/customers/${editingCustomer.id}`, cleanData);
            toast.success("Customer updated successfully!");
            setShowEditModal(false);
            setEditingCustomer(null);
            fetchCustomers();
        } catch (err) {
            toast.error(err.response?.data?.detail || "Failed to update customer");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <MobileLayout>
            <div className="p-4 max-w-lg mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <h1 className="text-2xl font-bold text-[#1A1A1A] font-['Montserrat']" data-testid="customers-title">
                        {customerTab === "customers" ? "Customers" : "Segments"}
                    </h1>
                    {customerTab === "customers" && (
                    <div className="flex gap-2">
                        {/* Sync button only shows when NOT in demo mode AND no customers exist */}
                        {!isDemoMode && !loading && customers.length === 0 && (
                            <Button 
                                onClick={() => navigate("/settings?tab=migration")}
                                variant="outline"
                                className="rounded-full h-10 px-4 border-[#3B82F6] text-[#3B82F6] hover:bg-[#3B82F6]/10"
                                data-testid="sync-mygenie-btn"
                            >
                                🔄 Sync MyGenie
                            </Button>
                        )}
                        <Button 
                            onClick={() => setShowAddModal(true)}
                            className="bg-[#F26B33] hover:bg-[#D85A2A] rounded-full h-10 px-4"
                            data-testid="add-customer-btn"
                        >
                            <Plus className="w-4 h-4 mr-1" /> Add
                        </Button>
                    </div>
                    )}
                </div>

                {/* Tab switcher */}
                <div className="flex gap-2 mb-4">
                    <button
                        onClick={() => setCustomerTab("customers")}
                        className={`flex-1 py-2 text-sm font-medium rounded-full transition-colors ${
                            customerTab === "customers"
                                ? "bg-[#1A1A1A] text-white"
                                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                        }`}
                        data-testid="tab-customers"
                    >
                        Customers
                    </button>
                    <button
                        onClick={() => setCustomerTab("segments")}
                        className={`flex-1 py-2 text-sm font-medium rounded-full transition-colors ${
                            customerTab === "segments"
                                ? "bg-[#1A1A1A] text-white"
                                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                        }`}
                        data-testid="tab-segments"
                    >
                        Segments
                    </button>
                </div>

                {customerTab === "customers" && (
                <>
                {/* Search & Filter Row */}
                <div className="flex gap-2 mb-3">
                    <div className="relative flex-1">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#A1A1AA]" />
                        <Input
                            type="text"
                            placeholder="Search by name or phone..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="search-input pl-12"
                            data-testid="customer-search-input"
                        />
                    </div>
                    <Button 
                        variant="outline" 
                        onClick={() => setShowFilters(true)}
                        className={`h-12 px-3 rounded-xl relative ${activeFiltersCount > 0 ? 'border-[#F26B33] text-[#F26B33]' : ''}`}
                        data-testid="filter-btn"
                    >
                        <Filter className="w-5 h-5" />
                        {activeFiltersCount > 0 && (
                            <span className="absolute -top-1 -right-1 w-5 h-5 bg-[#F26B33] text-white text-xs rounded-full flex items-center justify-center">
                                {activeFiltersCount}
                            </span>
                        )}
                    </Button>
                </div>

                {/* Quick Filter Chips */}
                <div className="flex gap-2 overflow-x-auto pb-3 mb-3 -mx-4 px-4 scrollbar-hide">
                    <button
                        onClick={() => setFilters({...filters, vip_flag: filters.vip_flag === "true" ? "all" : "true"})}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                            filters.vip_flag === "true" 
                                ? 'bg-amber-500 text-white' 
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                        data-testid="quick-filter-vip"
                    >
                        <Crown className="w-3 h-3" /> VIP
                    </button>
                    <button
                        onClick={() => setFilters({...filters, whatsapp_opt_in: filters.whatsapp_opt_in === "true" ? "all" : "true"})}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                            filters.whatsapp_opt_in === "true" 
                                ? 'bg-green-500 text-white' 
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                        data-testid="quick-filter-whatsapp"
                    >
                        <MessageCircle className="w-3 h-3" /> WhatsApp
                    </button>
                    <button
                        onClick={() => setFilters({...filters, has_birthday_this_month: !filters.has_birthday_this_month})}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                            filters.has_birthday_this_month 
                                ? 'bg-pink-500 text-white' 
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                        data-testid="quick-filter-birthday"
                    >
                        <Cake className="w-3 h-3" /> Birthday
                    </button>
                    <button
                        onClick={() => setFilters({...filters, diet_preference: filters.diet_preference === "veg" ? "all" : "veg"})}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                            filters.diet_preference === "veg" 
                                ? 'bg-green-600 text-white' 
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                        data-testid="quick-filter-veg"
                    >
                        <Leaf className="w-3 h-3" /> Veg
                    </button>
                    <button
                        onClick={() => setFilters({...filters, last_visit_days: filters.last_visit_days === "30" ? "all" : "30"})}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                            filters.last_visit_days === "30" 
                                ? 'bg-orange-500 text-white' 
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                        data-testid="quick-filter-inactive"
                    >
                        <Clock className="w-3 h-3" /> Inactive 30d
                    </button>
                    <button
                        onClick={() => setFilters({...filters, customer_type: filters.customer_type === "corporate" ? "all" : "corporate"})}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                            filters.customer_type === "corporate" 
                                ? 'bg-blue-500 text-white' 
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                        data-testid="quick-filter-corporate"
                    >
                        <Building2 className="w-3 h-3" /> Corporate
                    </button>
                </div>

                {/* Full Screen Filter Drawer */}
                {showFilters && (
                    <div className="fixed inset-0 bg-white z-50 flex flex-col" data-testid="filter-drawer">
                        {/* Header */}
                        <div className="flex items-center justify-between p-4 border-b sticky top-0 bg-white">
                            <button onClick={() => setShowFilters(false)} className="p-2 -ml-2">
                                <ChevronLeft className="w-5 h-5" />
                            </button>
                            <h2 className="text-lg font-semibold">Filters</h2>
                            {activeFiltersCount > 0 ? (
                                <button onClick={clearFilters} className="text-sm text-[#F26B33] font-medium">
                                    Clear all
                                </button>
                            ) : (
                                <div className="w-16"></div>
                            )}
                        </div>

                        {/* Filter Content */}
                        <ScrollArea className="flex-1">
                            <div className="p-4 space-y-2">
                                
                                {/* Basic Filters Group */}
                                <div className="border rounded-xl overflow-hidden">
                                    <button 
                                        onClick={() => toggleFilterGroup("basic")}
                                        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
                                    >
                                        <div className="flex items-center gap-2">
                                            <Users className="w-4 h-4 text-[#F26B33]" />
                                            <span className="font-medium text-sm">Basic Filters</span>
                                        </div>
                                        {expandedFilterGroups.includes("basic") ? (
                                            <ChevronUp className="w-4 h-4 text-gray-400" />
                                        ) : (
                                            <ChevronDown className="w-4 h-4 text-gray-400" />
                                        )}
                                    </button>
                                    {expandedFilterGroups.includes("basic") && (
                                        <div className="p-4 space-y-4 bg-white">
                                            <div>
                                                <Label className="text-xs text-[#52525B]">Tier</Label>
                                                <Select value={filters.tier} onValueChange={(v) => setFilters({...filters, tier: v})}>
                                                    <SelectTrigger className="h-10 mt-1">
                                                        <SelectValue placeholder="All tiers" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="all">All tiers</SelectItem>
                                                        <SelectItem value="Bronze">Bronze</SelectItem>
                                                        <SelectItem value="Silver">Silver</SelectItem>
                                                        <SelectItem value="Gold">Gold</SelectItem>
                                                        <SelectItem value="Platinum">Platinum</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div>
                                                <Label className="text-xs text-[#52525B]">Customer Type</Label>
                                                <Select value={filters.customer_type} onValueChange={(v) => setFilters({...filters, customer_type: v})}>
                                                    <SelectTrigger className="h-10 mt-1">
                                                        <SelectValue placeholder="All types" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="all">All types</SelectItem>
                                                        <SelectItem value="normal">Normal</SelectItem>
                                                        <SelectItem value="corporate">Corporate</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div>
                                                <Label className="text-xs text-[#52525B]">City</Label>
                                                <Input
                                                    type="text"
                                                    placeholder="Enter city..."
                                                    value={filters.city}
                                                    onChange={(e) => setFilters({...filters, city: e.target.value})}
                                                    className="h-10 mt-1"
                                                />
                                            </div>
                                            <div>
                                                <Label className="text-xs text-[#52525B]">Lead Source</Label>
                                                <Select value={filters.lead_source} onValueChange={(v) => setFilters({...filters, lead_source: v})}>
                                                    <SelectTrigger className="h-10 mt-1">
                                                        <SelectValue placeholder="All sources" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="all">All sources</SelectItem>
                                                        <SelectItem value="Walk-in">Walk-in</SelectItem>
                                                        <SelectItem value="Swiggy">Swiggy</SelectItem>
                                                        <SelectItem value="Zomato">Zomato</SelectItem>
                                                        <SelectItem value="Instagram">Instagram</SelectItem>
                                                        <SelectItem value="Facebook">Facebook</SelectItem>
                                                        <SelectItem value="Google">Google</SelectItem>
                                                        <SelectItem value="Referral">Referral</SelectItem>
                                                        <SelectItem value="WhatsApp">WhatsApp</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Activity & Engagement Group */}
                                <div className="border rounded-xl overflow-hidden">
                                    <button 
                                        onClick={() => toggleFilterGroup("activity")}
                                        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
                                    >
                                        <div className="flex items-center gap-2">
                                            <Clock className="w-4 h-4 text-blue-500" />
                                            <span className="font-medium text-sm">Activity & Engagement</span>
                                        </div>
                                        {expandedFilterGroups.includes("activity") ? (
                                            <ChevronUp className="w-4 h-4 text-gray-400" />
                                        ) : (
                                            <ChevronDown className="w-4 h-4 text-gray-400" />
                                        )}
                                    </button>
                                    {expandedFilterGroups.includes("activity") && (
                                        <div className="p-4 space-y-4 bg-white">
                                            <div>
                                                <Label className="text-xs text-[#52525B]">Inactive For (Win-back)</Label>
                                                <Select value={filters.last_visit_days} onValueChange={(v) => setFilters({...filters, last_visit_days: v})}>
                                                    <SelectTrigger className="h-10 mt-1">
                                                        <SelectValue placeholder="All customers" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="all">All customers</SelectItem>
                                                        <SelectItem value="7">7+ days</SelectItem>
                                                        <SelectItem value="14">14+ days</SelectItem>
                                                        <SelectItem value="30">30+ days</SelectItem>
                                                        <SelectItem value="60">60+ days</SelectItem>
                                                        <SelectItem value="90">90+ days</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div>
                                                <Label className="text-xs text-[#52525B]">Total Visits</Label>
                                                <Select value={filters.total_visits} onValueChange={(v) => setFilters({...filters, total_visits: v})}>
                                                    <SelectTrigger className="h-10 mt-1">
                                                        <SelectValue placeholder="Any" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="all">Any</SelectItem>
                                                        <SelectItem value="0">New (0 visits)</SelectItem>
                                                        <SelectItem value="1-5">1-5 visits</SelectItem>
                                                        <SelectItem value="6-10">6-10 visits</SelectItem>
                                                        <SelectItem value="10+">10+ visits</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Dining Preferences Group */}
                                <div className="border rounded-xl overflow-hidden">
                                    <button 
                                        onClick={() => toggleFilterGroup("dining")}
                                        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
                                    >
                                        <div className="flex items-center gap-2">
                                            <Utensils className="w-4 h-4 text-green-500" />
                                            <span className="font-medium text-sm">Dining Preferences</span>
                                        </div>
                                        {expandedFilterGroups.includes("dining") ? (
                                            <ChevronUp className="w-4 h-4 text-gray-400" />
                                        ) : (
                                            <ChevronDown className="w-4 h-4 text-gray-400" />
                                        )}
                                    </button>
                                    {expandedFilterGroups.includes("dining") && (
                                        <div className="p-4 space-y-4 bg-white">
                                            <div>
                                                <Label className="text-xs text-[#52525B]">Diet Preference</Label>
                                                <Select value={filters.diet_preference} onValueChange={(v) => setFilters({...filters, diet_preference: v})}>
                                                    <SelectTrigger className="h-10 mt-1">
                                                        <SelectValue placeholder="All" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="all">All</SelectItem>
                                                        <SelectItem value="veg">Vegetarian</SelectItem>
                                                        <SelectItem value="non_veg">Non-Vegetarian</SelectItem>
                                                        <SelectItem value="vegan">Vegan</SelectItem>
                                                        <SelectItem value="jain">Jain</SelectItem>
                                                        <SelectItem value="eggetarian">Eggetarian</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div>
                                                <Label className="text-xs text-[#52525B]">Preferred Time Slot</Label>
                                                <Select value={filters.preferred_time_slot} onValueChange={(v) => setFilters({...filters, preferred_time_slot: v})}>
                                                    <SelectTrigger className="h-10 mt-1">
                                                        <SelectValue placeholder="All" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="all">All</SelectItem>
                                                        <SelectItem value="breakfast">Breakfast (8-11 AM)</SelectItem>
                                                        <SelectItem value="lunch">Lunch (12-3 PM)</SelectItem>
                                                        <SelectItem value="evening">Evening (4-7 PM)</SelectItem>
                                                        <SelectItem value="dinner">Dinner (7-11 PM)</SelectItem>
                                                        <SelectItem value="late_night">Late Night (11 PM+)</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div>
                                                <Label className="text-xs text-[#52525B]">Dining Type</Label>
                                                <Select value={filters.preferred_dining_type} onValueChange={(v) => setFilters({...filters, preferred_dining_type: v})}>
                                                    <SelectTrigger className="h-10 mt-1">
                                                        <SelectValue placeholder="All" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="all">All</SelectItem>
                                                        <SelectItem value="Dine-In">Dine-In</SelectItem>
                                                        <SelectItem value="Takeaway">Takeaway</SelectItem>
                                                        <SelectItem value="Delivery">Delivery</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Marketing Permissions Group */}
                                <div className="border rounded-xl overflow-hidden">
                                    <button 
                                        onClick={() => toggleFilterGroup("marketing")}
                                        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
                                    >
                                        <div className="flex items-center gap-2">
                                            <MessageCircle className="w-4 h-4 text-purple-500" />
                                            <span className="font-medium text-sm">Marketing Permissions</span>
                                        </div>
                                        {expandedFilterGroups.includes("marketing") ? (
                                            <ChevronUp className="w-4 h-4 text-gray-400" />
                                        ) : (
                                            <ChevronDown className="w-4 h-4 text-gray-400" />
                                        )}
                                    </button>
                                    {expandedFilterGroups.includes("marketing") && (
                                        <div className="p-4 space-y-4 bg-white">
                                            <div>
                                                <Label className="text-xs text-[#52525B]">WhatsApp Opt-In</Label>
                                                <Select value={filters.whatsapp_opt_in} onValueChange={(v) => setFilters({...filters, whatsapp_opt_in: v})}>
                                                    <SelectTrigger className="h-10 mt-1">
                                                        <SelectValue placeholder="All" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="all">All</SelectItem>
                                                        <SelectItem value="true">Opted-In</SelectItem>
                                                        <SelectItem value="false">Not Opted-In</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Special Occasions Group */}
                                <div className="border rounded-xl overflow-hidden">
                                    <button 
                                        onClick={() => toggleFilterGroup("occasions")}
                                        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
                                    >
                                        <div className="flex items-center gap-2">
                                            <Cake className="w-4 h-4 text-pink-500" />
                                            <span className="font-medium text-sm">Special Occasions</span>
                                        </div>
                                        {expandedFilterGroups.includes("occasions") ? (
                                            <ChevronUp className="w-4 h-4 text-gray-400" />
                                        ) : (
                                            <ChevronDown className="w-4 h-4 text-gray-400" />
                                        )}
                                    </button>
                                    {expandedFilterGroups.includes("occasions") && (
                                        <div className="p-4 space-y-3 bg-white">
                                            <label className="flex items-center gap-3 p-3 rounded-lg border cursor-pointer hover:bg-gray-50 transition-colors">
                                                <Checkbox 
                                                    checked={filters.has_birthday_this_month}
                                                    onCheckedChange={(checked) => setFilters({...filters, has_birthday_this_month: checked})}
                                                />
                                                <div className="flex items-center gap-2">
                                                    <Cake className="w-4 h-4 text-pink-500" />
                                                    <span className="text-sm">Birthday this month</span>
                                                </div>
                                            </label>
                                            <label className="flex items-center gap-3 p-3 rounded-lg border cursor-pointer hover:bg-gray-50 transition-colors">
                                                <Checkbox 
                                                    checked={filters.has_anniversary_this_month}
                                                    onCheckedChange={(checked) => setFilters({...filters, has_anniversary_this_month: checked})}
                                                />
                                                <div className="flex items-center gap-2">
                                                    <Heart className="w-4 h-4 text-red-500" />
                                                    <span className="text-sm">Anniversary this month</span>
                                                </div>
                                            </label>
                                        </div>
                                    )}
                                </div>

                                {/* Flags & Status Group */}
                                <div className="border rounded-xl overflow-hidden">
                                    <button 
                                        onClick={() => toggleFilterGroup("flags")}
                                        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
                                    >
                                        <div className="flex items-center gap-2">
                                            <Flag className="w-4 h-4 text-red-500" />
                                            <span className="font-medium text-sm">Flags & Status</span>
                                        </div>
                                        {expandedFilterGroups.includes("flags") ? (
                                            <ChevronUp className="w-4 h-4 text-gray-400" />
                                        ) : (
                                            <ChevronDown className="w-4 h-4 text-gray-400" />
                                        )}
                                    </button>
                                    {expandedFilterGroups.includes("flags") && (
                                        <div className="p-4 space-y-4 bg-white">
                                            <div>
                                                <Label className="text-xs text-[#52525B]">VIP Status</Label>
                                                <Select value={filters.vip_flag} onValueChange={(v) => setFilters({...filters, vip_flag: v})}>
                                                    <SelectTrigger className="h-10 mt-1">
                                                        <SelectValue placeholder="All" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="all">All</SelectItem>
                                                        <SelectItem value="true">VIP Only</SelectItem>
                                                        <SelectItem value="false">Non-VIP</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div>
                                                <Label className="text-xs text-[#52525B]">Complaint Flag</Label>
                                                <Select value={filters.complaint_flag} onValueChange={(v) => setFilters({...filters, complaint_flag: v})}>
                                                    <SelectTrigger className="h-10 mt-1">
                                                        <SelectValue placeholder="All" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="all">All</SelectItem>
                                                        <SelectItem value="true">Has Complaints</SelectItem>
                                                        <SelectItem value="false">No Complaints</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div>
                                                <Label className="text-xs text-[#52525B]">Blacklist Status</Label>
                                                <Select value={filters.blacklist_flag} onValueChange={(v) => setFilters({...filters, blacklist_flag: v})}>
                                                    <SelectTrigger className="h-10 mt-1">
                                                        <SelectValue placeholder="All" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="all">All</SelectItem>
                                                        <SelectItem value="true">Blacklisted</SelectItem>
                                                        <SelectItem value="false">Not Blacklisted</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Sort Options Group */}
                                <div className="border rounded-xl overflow-hidden">
                                    <button 
                                        onClick={() => toggleFilterGroup("sort")}
                                        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
                                    >
                                        <div className="flex items-center gap-2">
                                            <TrendingUp className="w-4 h-4 text-gray-500" />
                                            <span className="font-medium text-sm">Sort Options</span>
                                        </div>
                                        {expandedFilterGroups.includes("sort") ? (
                                            <ChevronUp className="w-4 h-4 text-gray-400" />
                                        ) : (
                                            <ChevronDown className="w-4 h-4 text-gray-400" />
                                        )}
                                    </button>
                                    {expandedFilterGroups.includes("sort") && (
                                        <div className="p-4 space-y-4 bg-white">
                                            <div>
                                                <Label className="text-xs text-[#52525B]">Sort By</Label>
                                                <Select value={filters.sort_by} onValueChange={(v) => setFilters({...filters, sort_by: v})}>
                                                    <SelectTrigger className="h-10 mt-1">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="created_at">Date Added</SelectItem>
                                                        <SelectItem value="last_visit">Last Visit</SelectItem>
                                                        <SelectItem value="total_spent">Total Spent</SelectItem>
                                                        <SelectItem value="total_points">Points</SelectItem>
                                                        <SelectItem value="name">Name</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Saved Segments */}
                                {savedSegments.length > 0 && (
                                    <div className="border rounded-xl overflow-hidden">
                                        <div className="p-4 bg-gray-50">
                                            <div className="flex items-center gap-2">
                                                <Layers className="w-4 h-4 text-indigo-500" />
                                                <span className="font-medium text-sm">Saved Segments</span>
                                            </div>
                                        </div>
                                        <div className="p-4 space-y-2 bg-white">
                                            {savedSegments.map(segment => (
                                                <div key={segment.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                                    <button
                                                        onClick={() => {
                                                            loadSegment(segment);
                                                            setShowFilters(false);
                                                        }}
                                                        className="flex-1 text-left"
                                                    >
                                                        <p className="text-sm font-medium text-[#1A1A1A]">{segment.name}</p>
                                                        <p className="text-xs text-[#52525B]">{segment.customer_count} customers</p>
                                                    </button>
                                                    <button
                                                        onClick={() => deleteSegment(segment.id)}
                                                        className="ml-2 p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                            </div>
                        </ScrollArea>

                        {/* Footer with Apply Button */}
                        <div className="p-4 border-t bg-white sticky bottom-0 space-y-2">
                            {activeFiltersCount > 0 && (
                                <Button 
                                    onClick={() => {
                                        setShowSaveSegmentDialog(true);
                                    }}
                                    variant="outline"
                                    className="w-full h-11 rounded-xl border-[#F26B33] text-[#F26B33] hover:bg-[#F26B33]/5"
                                    data-testid="save-segment-btn"
                                >
                                    <Save className="w-4 h-4 mr-2" /> Save as Segment
                                </Button>
                            )}
                            <Button 
                                onClick={() => setShowFilters(false)}
                                className="w-full h-12 rounded-xl bg-[#F26B33] hover:bg-[#D85A2A] text-white font-semibold"
                                data-testid="apply-filters-btn"
                            >
                                Show {customers.length} Customers
                            </Button>
                        </div>
                    </div>
                )}

                {/* Save Segment Dialog */}
                {showSaveSegmentDialog && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4" onClick={() => setShowSaveSegmentDialog(false)}>
                        <div className="bg-white rounded-2xl p-6 w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
                            <h3 className="text-lg font-semibold mb-4">Save Segment</h3>
                            <div className="space-y-4">
                                <div>
                                    <Label className="text-sm font-medium">Segment Name</Label>
                                    <Input
                                        type="text"
                                        placeholder="e.g., VIP Customers"
                                        value={segmentName}
                                        onChange={(e) => setSegmentName(e.target.value)}
                                        className="mt-1 h-11 rounded-xl"
                                        data-testid="segment-name-input"
                                    />
                                </div>
                                <div className="bg-gray-50 p-3 rounded-lg max-h-40 overflow-y-auto">
                                    <p className="text-xs font-medium text-[#52525B] mb-2">Current Filters:</p>
                                    <div className="space-y-1 text-xs text-[#1A1A1A]">
                                        {filters.tier !== "all" && <p>• Tier: {filters.tier}</p>}
                                        {filters.customer_type !== "all" && <p>• Type: {filters.customer_type}</p>}
                                        {filters.last_visit_days !== "all" && <p>• Inactive: {filters.last_visit_days}+ days</p>}
                                        {filters.city && <p>• City: {filters.city}</p>}
                                        {filters.whatsapp_opt_in !== "all" && <p>• WhatsApp: {filters.whatsapp_opt_in === "true" ? "Opted-In" : "Not Opted"}</p>}
                                        {filters.vip_flag !== "all" && <p>• VIP: {filters.vip_flag === "true" ? "Yes" : "No"}</p>}
                                        {filters.diet_preference !== "all" && <p>• Diet: {filters.diet_preference}</p>}
                                        {filters.lead_source !== "all" && <p>• Source: {filters.lead_source}</p>}
                                        {filters.preferred_time_slot !== "all" && <p>• Time Slot: {filters.preferred_time_slot}</p>}
                                        {filters.preferred_dining_type !== "all" && <p>• Dining: {filters.preferred_dining_type}</p>}
                                        {filters.has_birthday_this_month && <p>• Birthday this month</p>}
                                        {filters.has_anniversary_this_month && <p>• Anniversary this month</p>}
                                        {filters.total_visits !== "all" && <p>• Visits: {filters.total_visits}</p>}
                                        {filters.complaint_flag !== "all" && <p>• Complaints: {filters.complaint_flag === "true" ? "Yes" : "No"}</p>}
                                        {filters.blacklist_flag !== "all" && <p>• Blacklist: {filters.blacklist_flag === "true" ? "Yes" : "No"}</p>}
                                        {search && <p>• Search: {search}</p>}
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        onClick={() => {
                                            setShowSaveSegmentDialog(false);
                                            setSegmentName("");
                                        }}
                                        className="flex-1"
                                    >
                                        Cancel
                                    </Button>
                                    <Button
                                        onClick={saveAsSegment}
                                        className="flex-1 bg-[#F26B33] hover:bg-[#D85A2A]"
                                        data-testid="save-segment-confirm-btn"
                                    >
                                        Save
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Segment Stats Bar */}
                {segments && (
                    <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
                        <div className="flex-shrink-0 px-3 py-1.5 bg-gray-100 rounded-full text-xs font-medium text-[#52525B]">
                            Total: {segments.total}
                        </div>
                        <div className="flex-shrink-0 px-3 py-1.5 bg-amber-50 rounded-full text-xs font-medium text-amber-700">
                            Bronze: {segments.by_tier?.bronze || 0}
                        </div>
                        <div className="flex-shrink-0 px-3 py-1.5 bg-gray-200 rounded-full text-xs font-medium text-gray-700">
                            Silver: {segments.by_tier?.silver || 0}
                        </div>
                        <div className="flex-shrink-0 px-3 py-1.5 bg-yellow-50 rounded-full text-xs font-medium text-yellow-700">
                            Gold: {segments.by_tier?.gold || 0}
                        </div>
                    </div>
                )}

                {/* Customer List */}
                {loading ? (
                    <div className="space-y-3">
                        {[1,2,3].map(i => (
                            <div key={i} className="customer-list-item animate-pulse">
                                <div className="w-10 h-10 rounded-full bg-gray-200 mr-3"></div>
                                <div className="flex-1">
                                    <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
                                    <div className="h-3 bg-gray-200 rounded w-20"></div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : customers.length === 0 ? (
                    <div className="empty-state">
                        <Users className="empty-state-icon" />
                        <p className="text-[#52525B]">{search || activeFiltersCount > 0 ? "No customers found" : "No customers yet"}</p>
                        {!search && activeFiltersCount === 0 && (
                            <Button 
                                onClick={() => setShowAddModal(true)}
                                className="mt-4 bg-[#F26B33] hover:bg-[#D85A2A] rounded-full"
                            >
                                Add your first customer
                            </Button>
                        )}
                        {activeFiltersCount > 0 && (
                            <Button 
                                onClick={clearFilters}
                                variant="outline"
                                className="mt-4 rounded-full"
                            >
                                Clear filters
                            </Button>
                        )}
                    </div>
                ) : (
                    <div className="space-y-2">
                        {customers.map((customer) => (
                            <div
                                key={customer.id}
                                className="customer-list-item w-full"
                                data-testid={`customer-row-${customer.id}`}
                            >
                                <Avatar className="w-10 h-10 mr-3">
                                    <AvatarFallback className={`font-semibold ${
                                        customer.customer_type === "corporate" 
                                            ? "bg-[#F26B33]/10 text-[#F26B33]" 
                                            : "bg-[#329937]/10 text-[#329937]"
                                    }`}>
                                        {customer.customer_type === "corporate" ? <Building2 className="w-5 h-5" /> : customer.name.charAt(0)}
                                    </AvatarFallback>
                                </Avatar>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <p className="font-medium text-[#1A1A1A] truncate">{customer.name} <span className="text-[#52525B] font-normal">({customer.total_visits || 0})</span></p>
                                        <button
                                            onClick={(e) => openEditModal(customer, e)}
                                            className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center hover:bg-[#F26B33]/10 transition-colors"
                                            data-testid={`edit-customer-list-${customer.id}`}
                                        >
                                            <Edit2 className="w-3 h-3 text-[#52525B]" />
                                        </button>
                                    </div>
                                    <p className="text-sm text-[#52525B]">{customer.country_code || '+91'} {customer.phone}</p>
                                </div>
                                <button 
                                    onClick={() => navigate(`/customers/${customer.id}`)}
                                    className="text-right flex items-center gap-3"
                                >
                                    <div className="text-right">
                                        <p className="font-semibold text-[#329937] points-display">{customer.total_points}</p>
                                        <Badge variant="outline" className={`tier-badge ${customer.tier.toLowerCase()}`}>
                                            {customer.tier}
                                        </Badge>
                                    </div>
                                    {customer.wallet_balance > 0 && (
                                        <div className="text-right border-l pl-3 border-gray-200">
                                            <p className="font-semibold text-[#F26B33]">₹{customer.wallet_balance.toLocaleString()}</p>
                                            <p className="text-[10px] text-[#A1A1AA]">Wallet</p>
                                        </div>
                                    )}
                                    <ChevronRight className="w-5 h-5 text-[#A1A1AA]" />
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </>
            )}
            </div>
            
            {customerTab === "segments" && (
                <SegmentsPageContent />
            )}

            {/* Add Customer Modal */}
            <Dialog open={showAddModal} onOpenChange={(open) => { setShowAddModal(open); if (!open) resetForm(); }}>
                <DialogContent className="max-w-lg mx-4 rounded-2xl max-h-[90vh] overflow-hidden flex flex-col">
                    <DialogHeader>
                        <DialogTitle className="font-['Montserrat']">Add New Customer</DialogTitle>
                        <DialogDescription>Enter customer details to start their loyalty journey.</DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleAddCustomer} className="flex-1 overflow-hidden">
                        <ScrollArea className="h-[calc(90vh-200px)] pr-4">
                            <Accordion type="multiple" defaultValue={["basic"]} className="w-full">
                                
                                {/* Basic Information - Always Expanded */}
                                <AccordionItem value="basic" className="border-b-0">
                                    <AccordionTrigger className="hover:no-underline py-3 px-3 bg-[#329937]/5 rounded-xl mb-2">
                                        <span className="flex items-center gap-2 text-sm font-semibold text-[#329937]">
                                            <User className="w-4 h-4" /> Basic Information
                                        </span>
                                    </AccordionTrigger>
                                    <AccordionContent className="px-1">
                                        <div className="space-y-4">
                                            <div>
                                                <Label htmlFor="name" className="form-label">Name *</Label>
                                                <Input
                                                    id="name"
                                                    value={newCustomer.name}
                                                    onChange={(e) => setNewCustomer({...newCustomer, name: e.target.value})}
                                                    placeholder="Customer name"
                                                    className="h-11 rounded-xl"
                                                    required
                                                    data-testid="new-customer-name"
                                                />
                                            </div>
                                            
                                            <div>
                                                <Label htmlFor="phone" className="form-label">Phone *</Label>
                                                <div className="flex gap-2">
                                                    <Select 
                                                        value={newCustomer.country_code} 
                                                        onValueChange={(v) => setNewCustomer({...newCustomer, country_code: v})}
                                                    >
                                                        <SelectTrigger className="w-24 h-11 rounded-xl" data-testid="country-code-select">
                                                            <SelectValue />
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            {COUNTRY_CODES.map(cc => (
                                                                <SelectItem key={cc.code} value={cc.code}>
                                                                    {cc.flag} {cc.code}
                                                                </SelectItem>
                                                            ))}
                                                        </SelectContent>
                                                    </Select>
                                                    <Input
                                                        id="phone"
                                                        type="tel"
                                                        value={newCustomer.phone}
                                                        onChange={(e) => setNewCustomer({...newCustomer, phone: e.target.value.replace(/\D/g, '')})}
                                                        placeholder="9876543210"
                                                        className="h-11 rounded-xl flex-1"
                                                        required
                                                        maxLength={10}
                                                        data-testid="new-customer-phone"
                                                    />
                                                </div>
                                            </div>

                                            <div>
                                                <Label htmlFor="email" className="form-label">Email</Label>
                                                <Input
                                                    id="email"
                                                    type="email"
                                                    value={newCustomer.email}
                                                    onChange={(e) => setNewCustomer({...newCustomer, email: e.target.value})}
                                                    placeholder="customer@email.com"
                                                    className="h-11 rounded-xl"
                                                    data-testid="new-customer-email"
                                                />
                                            </div>

                                            <div className="grid grid-cols-2 gap-3">
                                                <div>
                                                    <Label className="form-label">Gender</Label>
                                                    <Select 
                                                        value={newCustomer.gender} 
                                                        onValueChange={(v) => setNewCustomer({...newCustomer, gender: v})}
                                                    >
                                                        <SelectTrigger className="h-11 rounded-xl" data-testid="new-customer-gender">
                                                            <SelectValue placeholder="Select..." />
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            {GENDER_OPTIONS.map(opt => (
                                                                <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                                                            ))}
                                                        </SelectContent>
                                                    </Select>
                                                </div>
                                                <div>
                                                    <Label className="form-label">Language</Label>
                                                    <Select 
                                                        value={newCustomer.preferred_language} 
                                                        onValueChange={(v) => setNewCustomer({...newCustomer, preferred_language: v})}
                                                    >
                                                        <SelectTrigger className="h-11 rounded-xl" data-testid="new-customer-language">
                                                            <SelectValue placeholder="Select..." />
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            {LANGUAGE_OPTIONS.map(opt => (
                                                                <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                                                            ))}
                                                        </SelectContent>
                                                    </Select>
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-2 gap-3">
                                                <div>
                                                    <Label htmlFor="dob" className="form-label flex items-center gap-1">
                                                        <Calendar className="w-3.5 h-3.5" /> Date of Birth
                                                    </Label>
                                                    <Input
                                                        id="dob"
                                                        type="date"
                                                        value={newCustomer.dob}
                                                        onChange={(e) => setNewCustomer({...newCustomer, dob: e.target.value})}
                                                        className="h-11 rounded-xl"
                                                        data-testid="new-customer-dob"
                                                    />
                                                </div>
                                                <div>
                                                    <Label htmlFor="anniversary" className="form-label flex items-center gap-1">
                                                        <Calendar className="w-3.5 h-3.5" /> Anniversary
                                                    </Label>
                                                    <Input
                                                        id="anniversary"
                                                        type="date"
                                                        value={newCustomer.anniversary}
                                                        onChange={(e) => setNewCustomer({...newCustomer, anniversary: e.target.value})}
                                                        className="h-11 rounded-xl"
                                                        data-testid="new-customer-anniversary"
                                                    />
                                                </div>
                                            </div>

                                            {/* Customer Type */}
                                            <div>
                                                <Label className="form-label">Customer Type</Label>
                                                <div className="flex gap-2 mt-2">
                                                    <button
                                                        type="button"
                                                        onClick={() => setNewCustomer({...newCustomer, customer_type: "normal"})}
                                                        className={`flex-1 py-2.5 px-4 rounded-xl text-sm font-medium border-2 transition-all flex items-center justify-center gap-2 ${
                                                            newCustomer.customer_type === "normal"
                                                                ? "bg-[#329937] text-white border-[#329937]"
                                                                : "bg-white text-[#52525B] border-gray-200 hover:border-[#329937]"
                                                        }`}
                                                        data-testid="customer-type-normal"
                                                    >
                                                        <User className="w-4 h-4" /> Normal
                                                    </button>
                                                    <button
                                                        type="button"
                                                        onClick={() => setNewCustomer({...newCustomer, customer_type: "corporate"})}
                                                        className={`flex-1 py-2.5 px-4 rounded-xl text-sm font-medium border-2 transition-all flex items-center justify-center gap-2 ${
                                                            newCustomer.customer_type === "corporate"
                                                                ? "bg-[#F26B33] text-white border-[#F26B33]"
                                                                : "bg-white text-[#52525B] border-gray-200 hover:border-[#F26B33]"
                                                        }`}
                                                        data-testid="customer-type-corporate"
                                                    >
                                                        <Building2 className="w-4 h-4" /> Corporate
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </AccordionContent>
                                </AccordionItem>

                                {/* Address */}
                                <AccordionItem value="address" className="border-b-0">
                                    <AccordionTrigger className="hover:no-underline py-3 px-3 bg-cyan-50 rounded-xl mb-2">
                                        <span className="flex items-center gap-2 text-sm font-semibold text-cyan-600">
                                            <MapPin className="w-4 h-4" /> Address
                                        </span>
                                    </AccordionTrigger>
                                    <AccordionContent className="px-1">
                                        <div className="space-y-4">
                                            <div>
                                                <Label className="form-label">Address Line 1</Label>
                                                <Textarea 
                                                    placeholder="House/Flat No., Building..." 
                                                    className="rounded-xl resize-none" 
                                                    rows={2}
                                                    value={newCustomer.address}
                                                    onChange={(e) => setNewCustomer({...newCustomer, address: e.target.value})}
                                                />
                                            </div>
                                            <div>
                                                <Label className="form-label">Address Line 2</Label>
                                                <Input 
                                                    placeholder="Street, Area, Landmark" 
                                                    className="h-11 rounded-xl"
                                                    value={newCustomer.address_line_2}
                                                    onChange={(e) => setNewCustomer({...newCustomer, address_line_2: e.target.value})}
                                                />
                                            </div>
                                            <div className="grid grid-cols-2 gap-3">
                                                <div>
                                                    <Label className="form-label">City</Label>
                                                    <Input 
                                                        placeholder="City" 
                                                        className="h-11 rounded-xl"
                                                        value={newCustomer.city}
                                                        onChange={(e) => setNewCustomer({...newCustomer, city: e.target.value})}
                                                    />
                                                </div>
                                                <div>
                                                    <Label className="form-label">State</Label>
                                                    <Input 
                                                        placeholder="State" 
                                                        className="h-11 rounded-xl"
                                                        value={newCustomer.state}
                                                        onChange={(e) => setNewCustomer({...newCustomer, state: e.target.value})}
                                                    />
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-2 gap-3">
                                                <div>
                                                    <Label className="form-label">Pincode</Label>
                                                    <Input 
                                                        placeholder="400001" 
                                                        className="h-11 rounded-xl"
                                                        value={newCustomer.pincode}
                                                        onChange={(e) => setNewCustomer({...newCustomer, pincode: e.target.value})}
                                                    />
                                                </div>
                                                <div>
                                                    <Label className="form-label">Country</Label>
                                                    <Input 
                                                        placeholder="India" 
                                                        className="h-11 rounded-xl"
                                                        value={newCustomer.country}
                                                        onChange={(e) => setNewCustomer({...newCustomer, country: e.target.value})}
                                                    />
                                                </div>
                                            </div>
                                            <div>
                                                <Label className="form-label">Delivery Instructions</Label>
                                                <Textarea 
                                                    placeholder="Ring doorbell twice, leave at door..." 
                                                    className="rounded-xl resize-none" 
                                                    rows={2}
                                                    value={newCustomer.delivery_instructions}
                                                    onChange={(e) => setNewCustomer({...newCustomer, delivery_instructions: e.target.value})}
                                                />
                                            </div>
                                        </div>
                                    </AccordionContent>
                                </AccordionItem>

                                {/* Corporate Info - Only shows if customer_type is corporate */}
                                {newCustomer.customer_type === "corporate" && (
                                    <AccordionItem value="corporate" className="border-b-0">
                                        <AccordionTrigger className="hover:no-underline py-3 px-3 bg-[#F26B33]/10 rounded-xl mb-2">
                                            <span className="flex items-center gap-2 text-sm font-semibold text-[#F26B33]">
                                                <Building2 className="w-4 h-4" /> Corporate Info
                                            </span>
                                        </AccordionTrigger>
                                        <AccordionContent className="px-1">
                                            <div className="space-y-4">
                                                <div>
                                                    <Label className="form-label">Company/GST Name</Label>
                                                    <Input 
                                                        placeholder="Company name" 
                                                        className="h-11 rounded-xl"
                                                        value={newCustomer.gst_name}
                                                        onChange={(e) => setNewCustomer({...newCustomer, gst_name: e.target.value})}
                                                    />
                                                </div>
                                                <div>
                                                    <Label className="form-label">GST Number</Label>
                                                    <Input 
                                                        placeholder="22AAAAA0000A1Z5" 
                                                        className="h-11 rounded-xl"
                                                        value={newCustomer.gst_number}
                                                        onChange={(e) => setNewCustomer({...newCustomer, gst_number: e.target.value})}
                                                    />
                                                </div>
                                                <div>
                                                    <Label className="form-label">Billing Address</Label>
                                                    <Textarea 
                                                        placeholder="Billing address for invoices" 
                                                        className="rounded-xl resize-none" 
                                                        rows={2}
                                                        value={newCustomer.billing_address}
                                                        onChange={(e) => setNewCustomer({...newCustomer, billing_address: e.target.value})}
                                                    />
                                                </div>
                                                <div className="grid grid-cols-2 gap-3">
                                                    <div>
                                                        <Label className="form-label">Credit Limit</Label>
                                                        <Input 
                                                            placeholder="50000" 
                                                            type="number"
                                                            className="h-11 rounded-xl"
                                                            value={newCustomer.credit_limit}
                                                            onChange={(e) => setNewCustomer({...newCustomer, credit_limit: e.target.value})}
                                                        />
                                                    </div>
                                                    <div>
                                                        <Label className="form-label">Payment Terms</Label>
                                                        <Input 
                                                            placeholder="Net 30" 
                                                            className="h-11 rounded-xl"
                                                            value={newCustomer.payment_terms}
                                                            onChange={(e) => setNewCustomer({...newCustomer, payment_terms: e.target.value})}
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        </AccordionContent>
                                    </AccordionItem>
                                )}

                                {/* Source & Journey */}
                                {/* Dining Preferences & Special Occasions - Auto Detected */}
                                <AccordionItem value="ai-detected" className="border-b-0">
                                    <AccordionTrigger className="hover:no-underline py-3 px-3 bg-gradient-to-r from-rose-50 to-pink-50 rounded-xl mb-2">
                                        <span className="flex items-center gap-2 text-sm font-semibold text-rose-600">
                                            <Sparkles className="w-4 h-4" /> AI-Detected Preferences
                                            <span className="ml-auto text-[10px] bg-rose-100 text-rose-600 px-2 py-0.5 rounded-full">Auto</span>
                                        </span>
                                    </AccordionTrigger>
                                    <AccordionContent className="px-1">
                                        <div className="bg-gradient-to-br from-rose-50 to-pink-50 rounded-xl p-4 text-center">
                                            <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center mx-auto mb-3 shadow-sm">
                                                <Sparkles className="w-6 h-6 text-rose-500" />
                                            </div>
                                            <p className="font-semibold text-gray-800 text-sm">Smart Detection</p>
                                            <p className="text-xs text-gray-500 mt-2 leading-relaxed">
                                                Dining preferences, cuisine choices, spice levels, and festival preferences will be <strong>automatically detected</strong> from order history.
                                            </p>
                                            <div className="flex flex-wrap justify-center gap-2 mt-4">
                                                <span className="px-2 py-1 bg-white rounded-full text-[10px] text-gray-500 shadow-sm">Time Slot</span>
                                                <span className="px-2 py-1 bg-white rounded-full text-[10px] text-gray-500 shadow-sm">Cuisine</span>
                                                <span className="px-2 py-1 bg-white rounded-full text-[10px] text-gray-500 shadow-sm">Spice Level</span>
                                                <span className="px-2 py-1 bg-white rounded-full text-[10px] text-gray-500 shadow-sm">Festivals</span>
                                                <span className="px-2 py-1 bg-white rounded-full text-[10px] text-gray-500 shadow-sm">Diet</span>
                                            </div>
                                        </div>
                                    </AccordionContent>
                                </AccordionItem>
                                                {/* Tags & Flags */}
                                <AccordionItem value="flags" className="border-b-0">
                                    <AccordionTrigger className="hover:no-underline py-3 px-3 bg-indigo-50 rounded-xl mb-2">
                                        <span className="flex items-center gap-2 text-sm font-semibold text-indigo-600">
                                            <Star className="w-4 h-4" /> Tags & Flags
                                        </span>
                                    </AccordionTrigger>
                                    <AccordionContent className="px-1">
                                        <div className="space-y-3">
                                            <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-xl">
                                                <Label className="text-sm text-yellow-700">VIP Customer</Label>
                                                <Switch 
                                                    checked={newCustomer.vip_flag} 
                                                    onCheckedChange={(v) => setNewCustomer({...newCustomer, vip_flag: v})}
                                                />
                                            </div>
                                            <div className="flex items-center justify-between p-3 bg-red-50 rounded-xl">
                                                <Label className="text-sm text-red-700">Blacklisted</Label>
                                                <Switch 
                                                    checked={newCustomer.blacklist_flag} 
                                                    onCheckedChange={(v) => setNewCustomer({...newCustomer, blacklist_flag: v})}
                                                />
                                            </div>
                                            <div className="flex items-center justify-between p-3 bg-orange-50 rounded-xl">
                                                <Label className="text-sm text-orange-700">Complaint Flag</Label>
                                                <Switch 
                                                    checked={newCustomer.complaint_flag} 
                                                    onCheckedChange={(v) => setNewCustomer({...newCustomer, complaint_flag: v})}
                                                />
                                            </div>
                                        </div>
                                    </AccordionContent>
                                </AccordionItem>

                                {/* Contact Preferences - Coming Soon */}
                                <AccordionItem value="contact" className="border-b-0">
                                    <AccordionTrigger className="hover:no-underline py-3 px-3 bg-blue-50 rounded-xl mb-2">
                                        <span className="flex items-center gap-2 text-sm font-semibold text-blue-600">
                                            <Phone className="w-4 h-4" /> Contact Preferences
                                            <span className="ml-auto text-[10px] bg-blue-100 text-blue-500 px-2 py-0.5 rounded-full">Coming Soon</span>
                                        </span>
                                    </AccordionTrigger>
                                    <AccordionContent className="px-1">
                                        <ComingSoonOverlay color="blue">
                                            <div className="space-y-3 opacity-50">
                                                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                                                    <Label className="text-sm">WhatsApp Opt-in</Label>
                                                    <Switch disabled />
                                                </div>
                                                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                                                    <Label className="text-sm">Promo SMS Allowed</Label>
                                                    <Switch disabled checked />
                                                </div>
                                            </div>
                                        </ComingSoonOverlay>
                                    </AccordionContent>
                                </AccordionItem>

                                {/* Membership - Coming Soon */}
                                <AccordionItem value="membership" className="border-b-0">
                                    <AccordionTrigger className="hover:no-underline py-3 px-3 bg-purple-50 rounded-xl mb-2">
                                        <span className="flex items-center gap-2 text-sm font-semibold text-purple-600">
                                            <Tag className="w-4 h-4" /> Membership
                                            <span className="ml-auto text-[10px] bg-purple-100 text-purple-500 px-2 py-0.5 rounded-full">Coming Soon</span>
                                        </span>
                                    </AccordionTrigger>
                                    <AccordionContent className="px-1">
                                        <ComingSoonOverlay color="purple">
                                            <div className="space-y-4 opacity-50">
                                                <div>
                                                    <Label className="form-label">Membership ID</Label>
                                                    <Input placeholder="External membership ID" className="h-11 rounded-xl" disabled />
                                                </div>
                                                <div>
                                                    <Label className="form-label">Referral Code</Label>
                                                    <Input placeholder="Referral code" className="h-11 rounded-xl" disabled />
                                                </div>
                                            </div>
                                        </ComingSoonOverlay>
                                    </AccordionContent>
                                </AccordionItem>

                                {/* Source & Journey - Coming Soon */}
                                <AccordionItem value="source" className="border-b-0">
                                    <AccordionTrigger className="hover:no-underline py-3 px-3 bg-amber-50 rounded-xl mb-2">
                                        <span className="flex items-center gap-2 text-sm font-semibold text-amber-600">
                                            <TrendingUp className="w-4 h-4" /> Source & Journey
                                            <span className="ml-auto text-[10px] bg-amber-100 text-amber-500 px-2 py-0.5 rounded-full">Coming Soon</span>
                                        </span>
                                    </AccordionTrigger>
                                    <AccordionContent className="px-1">
                                        <ComingSoonOverlay color="amber">
                                            <div className="space-y-4 opacity-50">
                                                <div>
                                                    <Label className="form-label">Lead Source</Label>
                                                    <Input placeholder="How did they find you?" className="h-11 rounded-xl" disabled />
                                                </div>
                                                <div>
                                                    <Label className="form-label">Campaign Source</Label>
                                                    <Input placeholder="UTM or campaign" className="h-11 rounded-xl" disabled />
                                                </div>
                                            </div>
                                        </ComingSoonOverlay>
                                    </AccordionContent>
                                </AccordionItem>

                                {/* Custom Fields & Notes - Coming Soon */}
                                <AccordionItem value="custom" className="border-b-0">
                                    <AccordionTrigger className="hover:no-underline py-3 px-3 bg-gray-100 rounded-xl mb-2">
                                        <span className="flex items-center gap-2 text-sm font-semibold text-gray-600">
                                            <Layers className="w-4 h-4" /> Custom Fields & Notes
                                            <span className="ml-auto text-[10px] bg-gray-200 text-gray-500 px-2 py-0.5 rounded-full">Coming Soon</span>
                                        </span>
                                    </AccordionTrigger>
                                    <AccordionContent className="px-1">
                                        <ComingSoonOverlay color="gray">
                                            <div className="space-y-4 opacity-50">
                                                <div>
                                                    <Label className="form-label">Custom Field 1</Label>
                                                    <Input placeholder="Custom value..." className="h-11 rounded-xl" disabled />
                                                </div>
                                                <div>
                                                    <Label className="form-label">Notes</Label>
                                                    <Textarea placeholder="Special notes..." className="rounded-xl resize-none" rows={2} disabled />
                                                </div>
                                            </div>
                                        </ComingSoonOverlay>
                                    </AccordionContent>
                                </AccordionItem>

                            </Accordion>
                        </ScrollArea>
                        <DialogFooter className="gap-2 pt-4 border-t">
                            <Button 
                                type="button" 
                                variant="outline" 
                                onClick={() => { setShowAddModal(false); resetForm(); }}
                                className="rounded-full"
                            >
                                Cancel
                            </Button>
                            <Button 
                                type="submit" 
                                className="bg-[#F26B33] hover:bg-[#D85A2A] rounded-full"
                                disabled={submitting}
                                data-testid="submit-new-customer"
                            >
                                {submitting ? "Adding..." : "Add Customer"}
                            </Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Dialog>

            {/* Edit Customer Modal */}
            <Dialog open={showEditModal} onOpenChange={(open) => { setShowEditModal(open); if (!open) setEditingCustomer(null); }}>
                <DialogContent className="max-w-md mx-4 rounded-2xl max-h-[90vh] overflow-hidden">
                    <DialogHeader>
                        <DialogTitle className="font-['Montserrat']">Edit Customer</DialogTitle>
                        <DialogDescription>Update customer details</DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleUpdateCustomer}>
                        <ScrollArea className="h-[60vh] pr-4">
                            <div className="space-y-4 py-2">
                                <div>
                                    <Label className="form-label">Name *</Label>
                                    <Input
                                        value={editData.name || ""}
                                        onChange={(e) => setEditData({...editData, name: e.target.value})}
                                        placeholder="Customer name"
                                        className="h-11 rounded-xl"
                                        required
                                        data-testid="edit-list-name-input"
                                    />
                                </div>
                                
                                <div>
                                    <Label className="form-label">Phone Number * (Unique)</Label>
                                    <div className="flex gap-2">
                                        <Select 
                                            value={editData.country_code || "+91"} 
                                            onValueChange={(v) => setEditData({...editData, country_code: v})}
                                        >
                                            <SelectTrigger className="w-24 h-11 rounded-xl">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="+91">+91</SelectItem>
                                                <SelectItem value="+1">+1</SelectItem>
                                                <SelectItem value="+44">+44</SelectItem>
                                                <SelectItem value="+971">+971</SelectItem>
                                            </SelectContent>
                                        </Select>
                                        <Input
                                            value={editData.phone || ""}
                                            onChange={(e) => setEditData({...editData, phone: e.target.value})}
                                            placeholder="9876543210"
                                            className="flex-1 h-11 rounded-xl"
                                            required
                                            data-testid="edit-list-phone-input"
                                        />
                                    </div>
                                    <p className="text-xs text-[#52525B] mt-1">Phone number must be unique</p>
                                </div>

                                <div>
                                    <Label className="form-label">Email</Label>
                                    <Input
                                        type="email"
                                        value={editData.email || ""}
                                        onChange={(e) => setEditData({...editData, email: e.target.value})}
                                        placeholder="customer@email.com"
                                        className="h-11 rounded-xl"
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <Label className="form-label">Date of Birth</Label>
                                        <Input
                                            type="date"
                                            value={editData.dob || ""}
                                            onChange={(e) => setEditData({...editData, dob: e.target.value})}
                                            className="h-11 rounded-xl"
                                        />
                                    </div>
                                    <div>
                                        <Label className="form-label">Anniversary</Label>
                                        <Input
                                            type="date"
                                            value={editData.anniversary || ""}
                                            onChange={(e) => setEditData({...editData, anniversary: e.target.value})}
                                            className="h-11 rounded-xl"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <Label className="form-label">Customer Type</Label>
                                    <Select 
                                        value={editData.customer_type || "normal"} 
                                        onValueChange={(v) => setEditData({...editData, customer_type: v})}
                                    >
                                        <SelectTrigger className="h-11 rounded-xl">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="normal">Normal</SelectItem>
                                            <SelectItem value="corporate">Corporate</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                {editData.customer_type === "corporate" && (
                                    <>
                                        <div>
                                            <Label className="form-label">GST Name</Label>
                                            <Input
                                                value={editData.gst_name || ""}
                                                onChange={(e) => setEditData({...editData, gst_name: e.target.value})}
                                                placeholder="Company Name"
                                                className="h-11 rounded-xl"
                                            />
                                        </div>
                                        <div>
                                            <Label className="form-label">GST Number</Label>
                                            <Input
                                                value={editData.gst_number || ""}
                                                onChange={(e) => setEditData({...editData, gst_number: e.target.value})}
                                                placeholder="29ABCDE1234F1Z5"
                                                className="h-11 rounded-xl"
                                            />
                                        </div>
                                    </>
                                )}

                                <div>
                                    <Label className="form-label">City</Label>
                                    <Input
                                        value={editData.city || ""}
                                        onChange={(e) => setEditData({...editData, city: e.target.value})}
                                        placeholder="Mumbai"
                                        className="h-11 rounded-xl"
                                    />
                                </div>

                                <div>
                                    <Label className="form-label">Address</Label>
                                    <Input
                                        value={editData.address || ""}
                                        onChange={(e) => setEditData({...editData, address: e.target.value})}
                                        placeholder="Full address"
                                        className="h-11 rounded-xl"
                                    />
                                </div>

                                <div>
                                    <Label className="form-label">Notes</Label>
                                    <Input
                                        value={editData.notes || ""}
                                        onChange={(e) => setEditData({...editData, notes: e.target.value})}
                                        placeholder="Any special notes..."
                                        className="h-11 rounded-xl"
                                    />
                                </div>
                            </div>
                        </ScrollArea>
                        <DialogFooter className="mt-4">
                            <Button 
                                type="button" 
                                variant="outline" 
                                onClick={() => { setShowEditModal(false); setEditingCustomer(null); }}
                                className="rounded-full"
                            >
                                Cancel
                            </Button>
                            <Button 
                                type="submit" 
                                className="rounded-full bg-[#F26B33] hover:bg-[#D85A2A]"
                                disabled={submitting}
                                data-testid="save-edit-list-btn"
                            >
                                {submitting ? "Saving..." : "Save Changes"}
                            </Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Dialog>
        </MobileLayout>
    );
}
