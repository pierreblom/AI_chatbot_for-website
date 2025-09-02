<?php
/**
 * PHP Integration Example for Chatbot API
 * 
 * This class provides a simple PHP interface to interact with your chatbot API
 * Use this on your backend to proxy requests, add authentication, or integrate with your existing systems
 */

class ChatbotAPI {
    private $apiUrl;
    private $companyId;
    private $timeout;
    
    public function __construct($apiUrl, $companyId, $timeout = 30) {
        $this->apiUrl = rtrim($apiUrl, '/');
        $this->companyId = $companyId;
        $this->timeout = $timeout;
    }
    
    /**
     * Send a message to the chatbot
     */
    public function sendMessage($message, $sessionId = null) {
        if (empty($sessionId)) {
            $sessionId = 'session_' . uniqid() . '_' . time();
        }
        
        $data = [
            'message' => $message,
            'company_id' => $this->companyId,
            'session_id' => $sessionId
        ];
        
        return $this->makeRequest('POST', '/api/chat', $data);
    }
    
    /**
     * Scrape a website and add to knowledge base
     */
    public function scrapeWebsite($url, $maxDepth = 2, $includeLinks = true) {
        $data = [
            'url' => $url,
            'company_id' => $this->companyId,
            'max_depth' => $maxDepth,
            'include_links' => $includeLinks
        ];
        
        return $this->makeRequest('POST', '/api/scrape', $data);
    }
    
    /**
     * Add custom knowledge to the knowledge base
     */
    public function addKnowledge($content, $category = 'manual', $source = 'api', $metadata = []) {
        $data = [
            'company_id' => $this->companyId,
            'content' => $content,
            'category' => $category,
            'source' => $source,
            'metadata' => $metadata
        ];
        
        return $this->makeRequest('POST', '/api/knowledge/add', $data);
    }
    
    /**
     * Get all knowledge for the company
     */
    public function getKnowledge() {
        return $this->makeRequest('GET', '/api/knowledge/' . urlencode($this->companyId));
    }
    
    /**
     * Clear all knowledge for the company
     */
    public function clearKnowledge() {
        return $this->makeRequest('DELETE', '/api/knowledge/' . urlencode($this->companyId));
    }
    
    /**
     * Check API health
     */
    public function healthCheck() {
        return $this->makeRequest('GET', '/api/health');
    }
    
    /**
     * Make HTTP request to the API
     */
    private function makeRequest($method, $endpoint, $data = null) {
        $url = $this->apiUrl . $endpoint;
        
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => $this->timeout,
            CURLOPT_CUSTOMREQUEST => $method,
            CURLOPT_HTTPHEADER => [
                'Content-Type: application/json',
                'Accept: application/json'
            ]
        ]);
        
        if ($data && in_array($method, ['POST', 'PUT', 'PATCH'])) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        
        if ($error) {
            return [
                'success' => false,
                'error' => 'cURL error: ' . $error
            ];
        }
        
        $decodedResponse = json_decode($response, true);
        
        if ($httpCode >= 200 && $httpCode < 300) {
            return [
                'success' => true,
                'data' => $decodedResponse,
                'http_code' => $httpCode
            ];
        } else {
            return [
                'success' => false,
                'error' => $decodedResponse['error'] ?? 'HTTP error: ' . $httpCode,
                'http_code' => $httpCode
            ];
        }
    }
}

/**
 * WordPress Plugin Integration Example
 */
class WordPressChatbotIntegration {
    private $chatbot;
    
    public function __construct() {
        add_action('init', [$this, 'init']);
        add_action('wp_ajax_chatbot_send', [$this, 'handleChatAjax']);
        add_action('wp_ajax_nopriv_chatbot_send', [$this, 'handleChatAjax']);
        add_action('wp_footer', [$this, 'addChatbotScript']);
        add_shortcode('chatbot', [$this, 'chatbotShortcode']);
    }
    
    public function init() {
        $apiUrl = get_option('chatbot_api_url', 'http://localhost:5002');
        $companyId = get_option('chatbot_company_id', 'wordpress_site');
        $this->chatbot = new ChatbotAPI($apiUrl, $companyId);
    }
    
    public function handleChatAjax() {
        check_ajax_referer('chatbot_nonce', 'nonce');
        
        $message = sanitize_text_field($_POST['message']);
        $sessionId = sanitize_text_field($_POST['session_id'] ?? '');
        
        $response = $this->chatbot->sendMessage($message, $sessionId);
        
        wp_send_json($response);
    }
    
    public function addChatbotScript() {
        if (get_option('chatbot_enabled', true)) {
            ?>
            <script>
            // AJAX chatbot for WordPress
            class WordPressChatbot {
                constructor() {
                    this.sessionId = 'wp_session_' + Math.random().toString(36).substr(2, 9);
                    this.init();
                }
                
                async sendMessage(message) {
                    const response = await fetch('<?php echo admin_url('admin-ajax.php'); ?>', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: new URLSearchParams({
                            action: 'chatbot_send',
                            message: message,
                            session_id: this.sessionId,
                            nonce: '<?php echo wp_create_nonce('chatbot_nonce'); ?>'
                        })
                    });
                    return response.json();
                }
                
                init() {
                    // Initialize your chatbot widget here
                    console.log('WordPress Chatbot initialized');
                }
            }
            
            new WordPressChatbot();
            </script>
            <?php
        }
    }
    
    public function chatbotShortcode($atts) {
        $atts = shortcode_atts([
            'title' => 'Chat with us',
            'color' => '#0073aa',
            'position' => 'bottom-right'
        ], $atts);
        
        return sprintf(
            '<div id="chatbot-shortcode" data-title="%s" data-color="%s" data-position="%s"></div>',
            esc_attr($atts['title']),
            esc_attr($atts['color']),
            esc_attr($atts['position'])
        );
    }
}

// Initialize WordPress integration if in WordPress environment
if (defined('ABSPATH')) {
    new WordPressChatbotIntegration();
}

/**
 * Laravel Integration Example
 */

// routes/web.php or routes/api.php
/*
Route::post('/chatbot/send', [ChatbotController::class, 'sendMessage']);
Route::post('/chatbot/scrape', [ChatbotController::class, 'scrapeWebsite']);
Route::get('/chatbot/knowledge', [ChatbotController::class, 'getKnowledge']);
*/

// app/Http/Controllers/ChatbotController.php
/*
<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class ChatbotController extends Controller
{
    private $chatbot;
    
    public function __construct()
    {
        $this->chatbot = new ChatbotAPI(
            config('chatbot.api_url'),
            config('chatbot.company_id')
        );
    }
    
    public function sendMessage(Request $request)
    {
        $request->validate([
            'message' => 'required|string|max:1000',
            'session_id' => 'nullable|string'
        ]);
        
        $response = $this->chatbot->sendMessage(
            $request->message,
            $request->session_id ?: session()->getId()
        );
        
        return response()->json($response);
    }
    
    public function scrapeWebsite(Request $request)
    {
        $request->validate([
            'url' => 'required|url',
            'max_depth' => 'integer|min:1|max:5'
        ]);
        
        $response = $this->chatbot->scrapeWebsite(
            $request->url,
            $request->max_depth ?: 2
        );
        
        return response()->json($response);
    }
    
    public function getKnowledge()
    {
        $response = $this->chatbot->getKnowledge();
        return response()->json($response);
    }
}
*/

/**
 * Simple usage example
 */

// Example 1: Basic chatbot conversation
try {
    $chatbot = new ChatbotAPI('http://localhost:5002', 'my_company');
    
    // Add some knowledge first
    $result = $chatbot->addKnowledge(
        'We offer web development services starting at $5000. Contact us at info@company.com',
        'services',
        'manual'
    );
    
    if ($result['success']) {
        echo "Knowledge added successfully\n";
    }
    
    // Send a message
    $response = $chatbot->sendMessage('What services do you offer?');
    
    if ($response['success']) {
        echo "Bot: " . $response['data']['response'] . "\n";
    } else {
        echo "Error: " . $response['error'] . "\n";
    }
    
} catch (Exception $e) {
    echo "Exception: " . $e->getMessage() . "\n";
}

// Example 2: Website scraping
try {
    $chatbot = new ChatbotAPI('http://localhost:5002', 'scraped_company');
    
    $result = $chatbot->scrapeWebsite('https://example.com', 2, true);
    
    if ($result['success']) {
        echo "Scraped " . $result['data']['pages_scraped'] . " pages\n";
    } else {
        echo "Scraping failed: " . $result['error'] . "\n";
    }
    
} catch (Exception $e) {
    echo "Exception: " . $e->getMessage() . "\n";
}

// Example 3: AJAX endpoint for web integration
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_GET['action']) && $_GET['action'] === 'chatbot') {
    header('Content-Type: application/json');
    
    $input = json_decode(file_get_contents('php://input'), true);
    $message = $input['message'] ?? '';
    $sessionId = $input['session_id'] ?? session_id();
    
    if (empty($message)) {
        echo json_encode(['error' => 'Message is required']);
        exit;
    }
    
    $chatbot = new ChatbotAPI('http://localhost:5002', 'web_company');
    $response = $chatbot->sendMessage($message, $sessionId);
    
    echo json_encode($response);
    exit;
}

// Example 4: Bulk knowledge import
function importKnowledgeFromArray($chatbot, $knowledgeArray) {
    $results = [];
    
    foreach ($knowledgeArray as $item) {
        $result = $chatbot->addKnowledge(
            $item['content'],
            $item['category'] ?? 'general',
            $item['source'] ?? 'import',
            $item['metadata'] ?? []
        );
        
        $results[] = [
            'content' => substr($item['content'], 0, 50) . '...',
            'success' => $result['success'],
            'error' => $result['error'] ?? null
        ];
    }
    
    return $results;
}

// Usage
$knowledgeData = [
    [
        'content' => 'We are open Monday to Friday 9AM-6PM EST',
        'category' => 'hours',
        'source' => 'manual'
    ],
    [
        'content' => 'Free shipping on orders over $50',
        'category' => 'shipping',
        'source' => 'policy'
    ],
    [
        'content' => 'Our return policy allows 30-day returns',
        'category' => 'returns',
        'source' => 'policy'
    ]
];

$chatbot = new ChatbotAPI('http://localhost:5002', 'bulk_import_company');
$importResults = importKnowledgeFromArray($chatbot, $knowledgeData);

foreach ($importResults as $result) {
    echo "Imported: {$result['content']} - " . 
         ($result['success'] ? 'Success' : 'Failed: ' . $result['error']) . "\n";
}
?>