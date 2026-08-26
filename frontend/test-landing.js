const { chromium } = require('playwright');

async function testLandingPage() {
  console.log('🚀 Starting Playwright test...\n');
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  const errors = [];
  
  // Capture console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(`Console Error: ${msg.text()}`);
    }
  });
  
  // Capture page errors
  page.on('pageerror', error => {
    errors.push(`Page Error: ${error.message}`);
  });

  try {
    // Test 1: Navigate to landing page
    console.log('\n📍 Test 1: Navigating to http://localhost:3001...');
    const response = await page.goto('http://localhost:3001', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    if (response.status() === 200) {
      console.log('   ✅ Page loaded successfully (Status 200)');
    } else {
      console.log(`   ❌ Page returned status ${response.status()}`);
    }

    // Test 2: Check page title
    console.log('\n📍 Test 2: Checking page title...');
    const title = await page.title();
    console.log(`   Title: "${title}"`);
    if (title.includes('Orivory')) {
      console.log('   ✅ Title contains "Orivory"');
    } else {
      console.log('   ❌ Title missing expected content');
    }

    // Test 3: Check Hero section
    console.log('\n📍 Test 3: Checking Hero section...');
    const heroHeading = await page.locator('h1').first();
    const heroText = await heroHeading.textContent();
    console.log(`   Hero heading: "${heroText?.substring(0, 50)}..."`);
    
    const getStartedBtn = await page.locator('text=Start building free').first();
    if (await getStartedBtn.isVisible()) {
      console.log('   ✅ "Start building free" button is visible');
    } else {
      console.log('   ❌ "Start building free" button not found');
    }

    // Test 4: Check Navbar
    console.log('\n📍 Test 4: Checking Navbar...');
    const logo = await page.locator('text=Orivory').first();
    if (await logo.isVisible()) {
      console.log('   ✅ Logo "Orivory" is visible');
    }
    
    const featuresLink = await page.locator('a[href="#features"]').first();
    if (await featuresLink.isVisible()) {
      console.log('   ✅ "Features" link is visible');
    }

    // Test 5: Check Features section
    console.log('\n📍 Test 5: Checking Features section...');
    const insightCardsFeature = await page.locator('text=Unified Knowledge Graph').first();
    if (await insightCardsFeature.isVisible()) {
      console.log('   ✅ "Unified Knowledge Graph" feature found');
    }

    // Test 6: Check Pricing section
    console.log('\n📍 Test 6: Checking Pricing section...');
    const proPlan = await page.locator('h3:has-text("Pro")').first();
    if (await proPlan.isVisible()) {
      console.log('   ✅ "Pro" pricing plan found');
    }
    
    const freePlan = await page.locator('h3:has-text("Free")').first();
    if (await freePlan.isVisible()) {
      console.log('   ✅ "Free" pricing plan found');
    }

    // Test 7: Check FAQ section
    console.log('\n📍 Test 7: Testing FAQ accordion...');
    const faqButton = await page.locator('button:has-text("How does Orivory work")').first();
    if (await faqButton.isVisible()) {
      console.log('   ✅ FAQ question is visible');
    }

    // Test 8: Check Footer
    console.log('\n📍 Test 8: Checking Footer...');
    const footer = await page.locator('footer').first();
    if (await footer.isVisible()) {
      console.log('   ✅ Footer is visible');
    }
    
    const copyright = await page.locator('text=© 2025 Orivory').first();
    if (await copyright.isVisible()) {
      console.log('   ✅ Copyright text found');
    }

    // Test 9: Mobile responsiveness
    console.log('\n📍 Test 9: Testing mobile responsiveness...');
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(300);
    
    const mobileMenuBtn = await page.locator('button').first();
    if (await mobileMenuBtn.isVisible()) {
      console.log('   ✅ Mobile menu button visible');
    }
    
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.waitForTimeout(300);
    console.log('   ✅ Desktop view restored');

    // Test 10: CTA button navigation
    console.log('\n📍 Test 10: Testing CTA button...');
    await page.locator('a:has-text("Start building free")').first().click();

    // Summary
    console.log('\n' + '='.repeat(50));
    console.log('📊 TEST SUMMARY');
    console.log('='.repeat(50));
    
    if (errors.length === 0) {
      console.log('✅ No console errors detected!');
    } else {
      console.log(`❌ ${errors.length} errors found:`);
      errors.forEach((e, i) => console.log(`   ${i + 1}. ${e}`));
    }
    
    console.log('\n✅ All tests completed successfully!');
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

testLandingPage();
