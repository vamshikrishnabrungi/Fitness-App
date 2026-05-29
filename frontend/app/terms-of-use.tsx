/* eslint-disable react/no-unescaped-entities */
import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function TermsOfUseScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.closeButton}>
          <Ionicons name="close" size={26} color="#000000" />
        </TouchableOpacity>
      </View>
      <ScrollView
        style={styles.content}
        contentContainerStyle={{ paddingBottom: insets.bottom + 32 }}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.title}>SFTC TERMS OF USE</Text>
        <Text style={styles.paragraph}>Date of last revision: October 2025</Text>
        <Text style={styles.paragraph}>Welcome to the SFTC community!</Text>
        <Text style={styles.paragraph}>
          PLEASE READ THESE SFTC TERMS OF USE ("TERMS") CAREFULLY BEFORE USING ANY SFTC SERVICES OR
          PRODUCTS OR PARTICIPATING IN ANY SFTC EXPERIENCES.
        </Text>
        <Text style={styles.paragraph}>
          These Terms apply to the SFTC websites, social media platforms, and mobile apps (the
          "Platform"); the digital experiences, membership program(s), and other services accessible
          through or enabled by the Platform (together with the Platform, the "Services"); the footwear,
          apparel, equipment, accessories, and other products sold or otherwise provided by SFTC
          ("Products"); and the experiences and events hosted by SFTC or in SFTC stores ("Experiences").
        </Text>
        <Text style={styles.paragraph}>
          These Terms create a legally binding agreement between you and SFTC regarding your use of
          Services and Products and your participation in Experiences. If you live in any of the
          following countries or regions, additional or alternative provisions of these Terms (set forth
          below) may apply to you: Argentina, Australia, Brazil, Canada, Colombia, Hong Kong, Indonesia,
          Japan, Philippines, Thailand, Vietnam, and all European countries (including specific terms
          for Austria, Belgium, France, Germany, Hungary, Italy, Netherlands, Poland, Spain, Switzerland,
          and the United Kingdom). Additionally, in certain countries and regions, SFTC.com and/or the
          SFTC app may be operated by a third party on SFTC’s behalf, in which case such third party’s
          terms and conditions will apply to your use of those platforms in such countries or regions.
        </Text>
        <Text style={styles.paragraph}>
          When we say “SFTC,” “we,” “us,” or “our,” we are referring to the SFTC entity responsible for
          providing the Services, Products, or Experiences in your country or region. Please review our
          List of Local Entities for the SFTC entities responsible for providing the Services, Products
          and Experiences to you. You enter into these Terms with each applicable SFTC entity.
        </Text>

        <Text style={styles.heading}>1. TERMS APPLICABLE TO YOU</Text>
        <Text style={styles.subheading}>Updates</Text>
        <Text style={styles.paragraph}>
          We may update these Terms from time to time. The “date of last revision” above indicates when
          these Terms were last updated. If we make updates, we may also send you a notification. Unless
          we indicate otherwise, updated Terms will be effective immediately upon posting and your
          continued use of the Services, purchase of additional Products, or participation in
          Experiences will confirm your acceptance of the updates.
        </Text>
        <Text style={styles.subheading}>Supplemental Terms</Text>
        <Text style={styles.paragraph}>
          We may indicate that different or additional terms, conditions, guidelines, policies, or rules
          apply in relation to some of our Services, Products, or Experiences (“Supplemental Terms”).
          Any Supplemental Terms become part of your agreement with us if you use the applicable
          Services, Products or Experiences, and if there is a conflict between these Terms and the
          Supplemental Terms, the Supplemental Terms will control for that conflict. See the Section
          titled Alternative and Additional Terms for more information.
        </Text>
        <Text style={styles.subheading}>Terms of Sale</Text>
        <Text style={styles.paragraph}>
          By purchasing a Product from us, you also agree to the Terms of Sale that apply in your
          country or region. The Terms of Sale are Supplemental Terms. For information about how to
          return Products, see the Return Policy that applies in your country or region.
        </Text>
        <Text style={styles.subheading}>Privacy</Text>
        <Text style={styles.paragraph}>
          Our Privacy Policy describes how SFTC collects, uses, shares, and otherwise processes
          information about you.
        </Text>
        <Text style={styles.subheading}>Accessibility</Text>
        <Text style={styles.paragraph}>
          Our Digital Accessibility page explains how SFTC Services are accessible to all users,
          including individuals with disabilities.
        </Text>
        <Text style={styles.subheading}>Amateur Athlete Eligibility</Text>
        <Text style={styles.paragraph}>
          You are responsible for ensuring that your use of the Services and Products and your
          participation in Experiences does not affect your eligibility as an amateur athlete. Please
          check with your amateur athletic association for the rules that apply to you. SFTC is not
          responsible or liable if your use of the Services and Products or your participation in
          Experiences results in your ineligibility as an amateur athlete.
        </Text>

        <Text style={styles.heading}>2. GROUND RULES</Text>
        <Text style={styles.subheading}>Eligibility</Text>
        <Text style={styles.paragraph}>
          If you are younger than the legal age of majority where you live, you may only use the
          Services under the supervision of a parent or guardian who also agrees to these Terms. There
          may be additional age restrictions on Services or Experiences in certain countries or regions.
        </Text>
        <Text style={styles.subheading}>Account Registration</Text>
        <Text style={styles.paragraph}>
          When you register for an SFTC account, the following rules apply:
        </Text>
        <Text style={styles.listItem}>• Be True: Provide accurate registration information and keep your account information up to date.</Text>
        <Text style={styles.listItem}>• Be You: Your account is for your personal use only. Do not register for more than one account, register an account on behalf of someone else, or transfer your account to someone else.</Text>
        <Text style={styles.listItem}>• Be Secure: Keep your username, password, and other login credentials secure and do not allow anyone else to use your account.</Text>
        <Text style={styles.listItem}>• Be Responsible: Inform us immediately of any unauthorized use of your account. You are responsible for anything that happens through your account – with or without your permission.</Text>
        <Text style={styles.subheading}>Devices</Text>
        <Text style={styles.paragraph}>
          You may access the Services through a computer, mobile phone, tablet, console, or other
          technology (a “Device”). You agree to receive transactional and other emails, SMS and text
          messages from SFTC at the email address or other contact information you provide. Your
          carrier's normal data and text message rates and fees apply to your Device.
        </Text>

        <Text style={styles.heading}>3. SFTC CONTENT</Text>
        <Text style={styles.subheading}>Content We Own</Text>
        <Text style={styles.paragraph}>
          Except for your User Content (defined below), all of the content on our Services, including
          text, software, scripts, code, designs, graphics, photos, sounds, music, videos, applications,
          interactive features, articles, news stories, sketches, animations, stickers, general artwork
          and other content ("Content"), is owned by SFTC or our licensors and is protected by
          copyright, trademark, patent and other laws. Content is part of the Services, and you may
          only use the Services as expressly permitted by these Terms. SFTC reserves all rights not
          expressly granted to you in these Terms.
        </Text>
        <Text style={styles.paragraph}>
          The SFTC name, the logo design, our other logos, product or service names, slogans, and the
          look and feel of the Products and Services are trademarks, service marks, trade dress, or
          trade names owned or licensed by SFTC, and may not be copied, imitated, or used, in whole or
          in part, without our prior written permission. You do not acquire a license or any ownership
          rights to any trademarks, service marks, or trade names through your access or use of the
          Services. Do not change, obscure, or delete any ownership or proprietary notices appearing in
          the Services, including materials downloaded or printed from the Services.
        </Text>
        <Text style={styles.subheading}>License to Use</Text>
        <Text style={styles.paragraph}>
          Subject to your compliance with these Terms, SFTC grants you a limited, non-exclusive,
          non-transferable, non-sublicensable, revocable license to access and use our Services for your
          own personal, noncommercial use and, solely with respect to any applications included as part
          of the Services, to install and use such applications on Devices that you own or control. Any
          applications included in the Services are licensed (not sold), and if you fail to comply with
          any of the terms or conditions of these Terms, you must immediately cease using the Services
          and remove (uninstall and delete) applications included as part of the Services from your
          Devices.
        </Text>

        <Text style={styles.heading}>4. USER CONTENT</Text>
        <Text style={styles.subheading}>Content You Submit</Text>
        <Text style={styles.paragraph}>
          Some parts of the Services may allow you and other users to create, post, store, share, or
          otherwise provide content including photos, videos, and text (“User Content”). SFTC is not
          responsible for User Content. Except for the license you grant SFTC below, as between you and
          SFTC, you retain all rights in and to your User Content, excluding any portion of the
          Services included in your User Content.
        </Text>
        <Text style={styles.subheading}>License to Use</Text>
        <Text style={styles.paragraph}>
          You grant SFTC and its subsidiaries and affiliates a non-exclusive, perpetual, irrevocable,
          transferable, sub-licensable, royalty-free, worldwide and fully paid license to use,
          reproduce, modify, adapt, publish, translate, create derivative works from, distribute,
          publicly or otherwise perform and display, and exploit your User Content, including the
          likeness of any person that appears in the User Content and any of the concepts or ideas
          contained in the User Content, for any purpose, including commercial uses, in all media
          formats and channels now known or later developed without compensation to you or any third
          party.
        </Text>
        <Text style={styles.paragraph}>
          To the fullest extent permitted by applicable law, you hereby irrevocably waive any “moral
          rights” or other rights with respect to attribution of authorship or integrity of materials
          regarding your User Content that you may have under any applicable law or under any legal
          theory.
        </Text>
        <Text style={styles.subheading}>Right to User Content</Text>
        <Text style={styles.paragraph}>
          You represent and warrant that your User Content, and our use of such User Content as
          permitted by these Terms, will not violate any rights of any person or entity, including any
          third-party rights, or cause injury to any person or entity.
        </Text>

        <Text style={styles.heading}>5. FEEDBACK AND IDEAS</Text>
        <Text style={styles.paragraph}>
          We typically do not review unsolicited suggestions, ideas, feedback, or other materials that
          you post, submit, or otherwise communicate to us about SFTC or our Services, Products, or
          Experiences (collectively, “Feedback”). However, any Feedback you send us is provided on a
          non-confidential basis and you grant SFTC and its subsidiaries and affiliates a license to
          use such Feedback for any purpose, commercial or otherwise, without compensation or
          acknowledgement to you, including, but not limited to, for the purpose of developing,
          manufacturing, and marketing products and services.
        </Text>

        <Text style={styles.heading}>6. USER CODE OF CONDUCT</Text>
        <Text style={styles.paragraph}>
          We’re excited to have you contribute to the SFTC community. However, you are solely
          responsible for your conduct while using our Services or Products or participating in our
          Experiences and you must comply with the following rules:
        </Text>
        <Text style={styles.listItem}>
          • Be Yourself. Do not impersonate or otherwise misrepresent your affiliation with any person
          or organization, including athletes or SFTC employees. Only interact with the Services as
          yourself for personal, non-commercial purposes.
        </Text>
        <Text style={styles.listItem}>
          • Be Original. Do not create, post, store, or share any User Content if you do not have all
          the rights necessary to grant us the license described above.
        </Text>
        <Text style={styles.listItem}>
          • Be Safe. Take precautions when interacting with other users (including users you do not
          know) on the Services.
        </Text>
        <Text style={styles.listItem}>
          • Be Considerate. Do not do anything that may expose SFTC or its users to any type of harm.
        </Text>
        <Text style={styles.listItem}>
          • Be Respectful. You may only use the Services for their intended and authorized purposes.
        </Text>
        <Text style={styles.listItem}>
          • Be Appropriate. Respect the community and do not post User Content, link to a website, or
          do anything that is illegal, misleading, malicious, harassing, inaccurate, discriminatory, or
          otherwise objectionable or inappropriate or which violates any applicable laws.
        </Text>

        <Text style={styles.heading}>7. COPYRIGHT INFRINGEMENT</Text>
        <Text style={styles.paragraph}>
          SFTC has adopted a policy of terminating, in appropriate circumstances, the accounts of users
          found to infringe the intellectual property rights of others. If you believe that any Content
          on the Services infringes a copyright that you own or control, you may provide us with written
          notification at the address set forth below. Please see Section 512(c)(3) of the Digital
          Millennium Copyright Act (“DMCA”) for the requirements of a proper notification. If your
          complaint fails to provide everything specified in the DMCA, we may be unable to act on it.
        </Text>
        <Text style={styles.paragraph}>
          Please consult your legal advisor before filing a notice of copyright infringement with us
          because there may be penalties for false claims.
        </Text>
        <Text style={styles.paragraph}>
          Send copyright infringement complaints to: Copyright Agent, SFTC, Inc., One SFTC Drive,
          Beaverton, OR 97005, Telephone: 503-671-6453, Enforcement@sftc.com
        </Text>

        <Text style={styles.heading}>8. PARTNERS ON THE PLATFORM</Text>
        <Text style={styles.paragraph}>
          From time to time, SFTC may link to, provide information about, partner with, or allow you to
          connect your SFTC account with third-party websites, social media platforms, mobile apps, and
          other products, services, and experiences (“Third Parties”). You may be able to connect with
          these Third Parties through the Services or Products, or at Experiences, but this does not
          mean SFTC endorses, monitors, or has any control over these Third Parties or their activities.
          We provide information about and links to Third Parties as a service to those interested in
          such content. SFTC is not responsible for the content, policies, or activities of Third
          Parties and you interact with Third Parties at your own risk.
        </Text>

        <Text style={styles.heading}>9. PHYSICAL ACTIVITY & SAFETY</Text>
        <Text style={styles.paragraph}>
          The Services and Experiences may include features that provide information about physical
          activity, nutrition, or general wellness or provide opportunities to engage in physical
          activity. Content and information provided through the Services and at Experiences are
          provided for educational and informational purposes only and are not intended as medical
          advice. The Services and Products are not medical devices and are not intended to diagnose,
          treat, cure, or prevent any illness, metabolic disorder, disease, or health problem.
        </Text>
        <Text style={styles.paragraph}>
          Before using the Services or Products as part of any exercise program or participating in an
          Experience, consider the risks involved and consult with a medical professional.
        </Text>
        <Text style={styles.paragraph}>
          YOU ASSUME THE RISKS ASSOCIATED WITH ANY PHYSICAL ACTIVITIES THAT YOU ENGAGE IN.
        </Text>

        <Text style={styles.heading}>10. INDEMNIFICATION</Text>
        <Text style={styles.paragraph}>
          To the fullest extent permitted by applicable law, you agree to and will indemnify and hold
          harmless SFTC, Inc. and its subsidiaries and affiliates and each of its and their respective
          officers, directors, shareholders, employees, agents, distributors, representatives,
          contractors, licensors, suppliers, successors, assigns, and insurers, and all Experience
          sponsors, advertisers, volunteers, staff, and owners or lessors of premises used in connection
          with an Experience (individually and collectively, the “SFTC Parties”) from and against all
          claims, losses, liabilities, expenses, damages and costs, including attorneys' fees, arising
          from or relating in any way to (i) your access to or use of the Services or Products; (ii) your
          access to or participation in Experiences; (iii) your User Content or Feedback; or (iv) your
          violation of these Terms, any law or the rights of any third party (including intellectual
          property rights or privacy rights). The SFTC Parties will have control of the defense or
          settlement, at the SFTC Parties' sole option, of any third-party claims. This indemnity is in
          addition to, and not in lieu of, any other indemnities set forth in a written agreement
          between you and SFTC or the other SFTC Parties.
        </Text>

        <Text style={styles.heading}>11. RELEASE</Text>
        <Text style={styles.paragraph}>
          To the fullest extent permitted by applicable law, you, for yourself and on behalf of your
          heirs, estate, insurers, successors, and assigns, hereby fully and forever release and
          discharge the SFTC Parties from any and all claims or causes of action you may have for
          damages arising from or relating to these Terms, the Services, Products, or Experiences.
        </Text>

        <Text style={styles.heading}>12. WARRANTIES; DISCLAIMERS</Text>
        <Text style={styles.paragraph}>
          Your use of our Services and Products and your participation in Experiences, and any content
          or materials provided therein or therewith is at your sole risk. Except as otherwise provided
          in a writing by us and to the fullest extent permitted under applicable law, our Products,
          Services, Experiences and any content or materials provided therein or therewith are provided
          “AS IS” and “AS AVAILABLE” without any representation or warranties of any kind, whether
          express, implied, or statutory. We aren’t making any promises of any kind, and SFTC disclaims
          all warranties with respect to the foregoing, including implied warranties of merchantability,
          fitness for a particular purpose, title, and non-infringement.
        </Text>

        <Text style={styles.heading}>13. LIMITATION OF LIABILITY</Text>
        <Text style={styles.paragraph}>
          TO THE FULLEST EXTENT PERMITTED BY APPLICABLE LAW, NEITHER SFTC NOR ANY OF THE SFTC PARTIES
          WILL BE LIABLE TO YOU UNDER ANY THEORY OF LIABILITY, WHETHER BASED IN CONTRACT, TORT,
          NEGLIGENCE, STRICT LIABILITY, WARRANTY, STATUTE, OR OTHERWISE, FOR ANY DIRECT, SPECIAL,
          INCIDENTAL, INDIRECT, EXEMPLARY OR CONSEQUENTIAL DAMAGES, INCLUDING, WITHOUT LIMITATION, FOR
          ANY LOST PROFITS OR LOST DATA, ARISING OUT OF OR RELATING TO THESE TERMS, THE PRODUCTS,
          SERVICES, OR EXPERIENCES, EVEN IF SFTC HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
          YOU ASSUME TOTAL RESPONSIBILITY FOR YOUR USE OF THE PRODUCTS AND SERVICES AND YOUR
          PARTICIPATION IN EXPERIENCES.
        </Text>
        <Text style={styles.paragraph}>
          IF SFTC OR ONE OF THE OTHER SFTC PARTIES IS FOUND TO BE LIABLE TO YOU FOR ANY DAMAGE OR LOSS
          ARISING OUT OF OR RELATING TO THESE TERMS, THE PRODUCTS, SERVICES, OR EXPERIENCES, THE
          MAXIMUM AGGREGATE LIABILITY OF SFTC AND THE OTHER SFTC PARTIES SHALL NOT EXCEED THE LESSER OF
          (I) US $100.00 (OR THE EQUIVALENT OF US $100.00 IN THE LEGAL CURRENCY OF YOUR COUNTRY OR
          REGION) OR, IF YOU LIVE IN EUROPE, EURO €100.00; AND (II) THE AMOUNT PAID BY YOU TO SFTC FOR
          THE APPLICABLE SERVICES, PRODUCTS, OR EXPERIENCES GIVING RISE TO SUCH LIABILITY.
        </Text>
        <Text style={styles.paragraph}>
          THIS LIMITATION OF LIABILITY SECTION APPLIES WHETHER THE ALLEGED LIABILITY IS BASED IN
          CONTRACT, TORT, NEGLIGENCE, STRICT LIABILITY, WARRANTY, STATUTE, OR ANY OTHER BASIS, EVEN IF
          SFTC HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
        </Text>

        <Text style={styles.heading}>14. MODIFICATION AND TERMINATION</Text>
        <Text style={styles.paragraph}>
          SFTC may terminate or modify all or part of any Services, including member programs, Product
          offerings, and Experiences at any time without notice. All modifications and additions to the
          Services, Product offerings, and Experiences will be governed by these Terms, unless otherwise
          expressly stated by SFTC in writing.
        </Text>
        <Text style={styles.paragraph}>
          SFTC may terminate or suspend your account, delete your profile or any of your User Content,
          and restrict your use of all or any part of the Services or your ability to participate in
          Experiences at any time and for any reason, without any liability to SFTC, subject to
          applicable law.
        </Text>
        <Text style={styles.paragraph}>
          These Terms remain in effect even after your account is closed, terminated, or suspended or
          you have otherwise stopped using the Services and stopped participating in Experiences.
        </Text>

        <Text style={styles.heading}>15. ALTERNATIVE AND ADDITIONAL TERMS</Text>
        <Text style={styles.paragraph}>
          In addition to these Terms, additional terms and conditions, including the following
          Supplemental Terms, may apply to your use of certain Services or Products, or participation in
          Experiences:
        </Text>
        <Text style={styles.listItem}>• Launch Terms</Text>
        <Text style={styles.listItem}>• SFTC Gift Card Terms and Conditions</Text>
        <Text style={styles.listItem}>• SFTC Promo Code Terms and Conditions</Text>
        <Text style={styles.listItem}>• SFTC Consumer Ratings and Reviews Terms of Service</Text>
        <Text style={styles.listItem}>• Terms of Sale applicable in your country or region</Text>

        <Text style={styles.heading}>16. DISPUTES, JURISDICTION, VENUE</Text>
        <Text style={styles.subheading}>Applicable Law</Text>
        <Text style={styles.paragraph}>
          Any disputes, claims, controversies, or legal proceedings arising out of or relating to these
          Terms, the Products, Services, or Experiences (each a “Claim”) will be governed by and in all
          respects construed and enforced in accordance with Oregon law, except to the extent preempted
          by U.S. federal law, without regard to conflict of law rules or principles that would cause
          the application of the laws of any other jurisdiction. The U.N. Convention on Contracts for
          the International Sale of Goods will not apply.
        </Text>
        <Text style={styles.subheading}>Venue</Text>
        <Text style={styles.paragraph}>
          Except where prohibited by applicable law, and without limitation to any statutory rights for
          consumers, all Claims shall be resolved individually, without resort to any form of class
          action or any other kind of representative proceeding, and exclusively in the state or
          federal courts located in Multnomah County, Oregon, USA. You and SFTC waive any objection to
          venue in any such courts.
        </Text>
        <Text style={styles.subheading}>Time to Bring a Claim</Text>
        <Text style={styles.paragraph}>
          To the extent permitted by law, a Claim must be brought within one (1) year after the Claim
          arises; otherwise, the Claim is permanently barred, which means that you or SFTC will no
          longer have the right to assert that Claim against the other.
        </Text>

        <Text style={styles.heading}>17. MISCELLANEOUS</Text>
        <Text style={styles.subheading}>Export Restriction</Text>
        <Text style={styles.paragraph}>
          You may not use or otherwise export or re-export the Products, Services or related technology
          or any content contained therein, except as authorized by export control and sanctions laws of
          the United States and any other government having jurisdiction.
        </Text>
        <Text style={styles.subheading}>Electronic Communications</Text>
        <Text style={styles.paragraph}>
          By using the Services, purchasing Products, or participating in Experiences, you agree to
          receive certain electronic communications from SFTC, subject to applicable law. Communications
          and transactions between SFTC and you may be conducted electronically.
        </Text>
        <Text style={styles.subheading}>Assignment</Text>
        <Text style={styles.paragraph}>
          SFTC may assign its rights and duties under these Terms, in whole or in part, to any party at
          any time without notice to you, unless notice to you is required by applicable law, but this
          will not affect your rights or our obligations under these Terms. You cannot assign your
          rights and duties under these Terms, and any attempted assignment in violation of this
          sentence is void.
        </Text>
        <Text style={styles.subheading}>Waiver</Text>
        <Text style={styles.paragraph}>
          SFTC’s failure to insist upon or enforce strict performance of these Terms is not a waiver of
          any of these Terms or SFTC’s rights. You should always assume these Terms apply.
        </Text>
        <Text style={styles.subheading}>Severability</Text>
        <Text style={styles.paragraph}>
          If any provision in these Terms is held unlawful, invalid, or unenforceable for any reason,
          including because it is found to be unconscionable, then (i) the unenforceable or unlawful
          provision will be severed from these Terms; (ii) severance of the unenforceable or unlawful
          provision will have no impact whatsoever on the remainder of these Terms; and (iii) the
          unenforceable or unlawful provision may be revised to the extent required to render these
          Terms enforceable or valid, and the rights and responsibilities of the parties will be
          interpreted and enforced accordingly, so as to preserve these Terms and the intent of these
          Terms to the fullest possible extent.
        </Text>
        <Text style={styles.subheading}>Intended Beneficiary</Text>
        <Text style={styles.paragraph}>
          Except as otherwise provided herein, these Terms are intended solely for the benefit of the
          parties and are not intended to confer third-party beneficiary rights upon any other person
          or entity.
        </Text>
        <Text style={styles.subheading}>Section Headings</Text>
        <Text style={styles.paragraph}>
          The Section headings in these Terms are for convenience only and have no legal or contractual
          effect. Use of the word “including” will be interpreted to mean “including without
          limitation.”
        </Text>
        <Text style={styles.paragraph}>Thanks for reading. Please enjoy our community!</Text>

        <Text style={styles.heading}>COUNTRY/REGION SPECIFIC TERMS</Text>
        <Text style={styles.paragraph}>
          If you live in one of the following countries or regions these additional terms apply and/or
          supersede any inconsistent terms in the Terms of Use, as described below.
        </Text>
        <Text style={styles.subheading}>ARGENTINA</Text>
        <Text style={styles.paragraph}>
          Section 16 (DISPUTES, JURISDICTION, VENUE): The subsections titled “Applicable Law” and “Venue”
          are deleted and replaced with the following: Applicable Law/Venue. You agree that the Terms,
          Products, Services, Experiences, and any dispute between you and SFTC arising therefrom shall
          be governed in all respects by Argentine law.
        </Text>
        <Text style={styles.subheading}>AUSTRALIA</Text>
        <Text style={styles.paragraph}>
          Section 4 (USER CONTENT): The second paragraph in the subsection titled “License to Use” is
          deleted and replaced with the following: You hereby irrevocably waive or give your consent to
          SFTC doing or not doing anything that may otherwise infringe any of your “moral rights” or
          other rights with respect to attribution of authorship or integrity of materials regarding
          your User Content that you may have under any applicable law or under any legal theory.
        </Text>
        <Text style={styles.paragraph}>
          Section 10 (INDEMNIFICATION): This section is deleted and replaced with the following: Nothing
          in these Terms will be read or applied so as to exclude, restrict or modify or have the effect
          of excluding, restricting or modifying any right or remedy implied by or contained in the
          Australian Consumer Law (“ACL”) and which by law cannot be excluded, restricted or modified,
          even if any other term of these Terms would otherwise suggest that this might be the case. To
          the maximum extent permitted by applicable law (including the ACL), you agree to indemnify,
          defend, and hold harmless the SFTC Parties from and against all reasonable claims, losses,
          liabilities, expenses, damages and costs, including, without limitation, attorneys' fees,
          arising from or relating in any way to your User Content, your misuse of the Services,
          Products or Experiences or any contravention of law by you, other than to the extent to which
          a SFTC Party or a third party contributed to or caused the loss.
        </Text>
        <Text style={styles.paragraph}>
          Section 11 (RELEASE): This section is deleted and not replaced. Section 12 (WARRANTIES;
          DISCLAIMERS): This section is modified by adding the following at the end of the section:
          However, the Services, Content, and the materials and products contained therein come with
          certain guarantees that cannot be excluded for the benefit of Australian customers under the
          ACL. Section 13 (LIMITATION OF LIABILITY): This section is deleted and replaced with the
          following: TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, AND WITHOUT EXCLUDING OR
          LIMITING ANY RIGHTS UNDER THE ACL WHICH CANNOT LAWFULLY BE EXCLUDED OR LIMITED, NONE OF THE
          SFTC PARTIES WILL BE LIABLE FOR ANY DIRECT, SPECIAL, INCIDENTAL, INDIRECT OR CONSEQUENTIAL
          DAMAGES, INCLUDING WITHOUT LIMITATION FOR ANY LOST PROFITS OR LOST DATA, ARISING OUT OF OR
          RELATING TO THESE TERMS, THE SERVICES, PRODUCTS, OR EXPERIENCES, EVEN IF SFTC HAS BEEN ADVISED
          OF THE POSSIBILITY OF SUCH DAMAGES.
        </Text>
        <Text style={styles.paragraph}>
          Section 16 (DISPUTES, JURISDICTION, VENUE): The subsection titled “Venue” is deleted and
          replaced with the following: Except where prohibited by applicable law, including the ACL,
          you agree that all Claims shall be resolved exclusively in the state or federal courts located
          in Multnomah County, Oregon, USA.
        </Text>
        <Text style={styles.paragraph}>
          The subsection titled “Time to Bring a Claim” is deleted and not replaced.
        </Text>
        <Text style={styles.subheading}>BRAZIL</Text>
        <Text style={styles.paragraph}>
          Section 16 (DISPUTES, JURISDICTION, VENUE): The subsections titled “Applicable Law” and “Venue”
          are deleted and replaced with the following: Applicable Law/Venue. You agree that the Terms,
          Products, Services, Experiences, and any dispute between you and SFTC arising therefrom shall
          be governed in all respects by Brazilian law, without regard to choice of law provisions, and
          not by the 1980 U.N. Convention on Contracts for the International Sale of Goods. Except where
          prohibited, you agree that all disputes, claims and legal proceedings directly or indirectly
          arising out of or relating to the Terms, Products, Services, and/or Experiences shall be
          resolved individually, without resort to any form of class action, and exclusively in Brazil.
        </Text>
        <Text style={styles.subheading}>CANADA</Text>
        <Text style={styles.paragraph}>
          Section 1 (TERMS APPLICABLE TO YOU): The subsection titled “Updates” is qualified by the
          following: (1) If required by applicable law, SFTC will send to you, at least 30 days before
          the amendment comes into force, a written notice drawn up clearly and legibly, setting out the
          new clause and the date of the coming into force of the amendment; and (2) In such case, you
          may refuse the amendment and rescind or, in the case of a contract involving sequential
          performance, cancel the contract without cost, penalty or cancellation indemnity by sending
          SFTC a notice to that effect no later than 30 days after the amendment comes into force, if
          the amendment entails an increase in your obligations or a reduction in SFTC's obligations.
        </Text>
        <Text style={styles.paragraph}>
          Multiple Sections: The terms set forth in Sections 9, 10, 12, and 13 are qualified by the
          following: Consumer protection laws in some jurisdictions, which may include Quebec, do not
          allow for the limitations and exclusions of warranties on purchased products or services.
        </Text>
        <Text style={styles.paragraph}>
          Section 16 (DISPUTES, JURISDICTION, VENUE): This section is modified by adding the following
          at the beginning of the section: Consumer protection laws in some jurisdictions, which may
          include Quebec, might require that your agreement be governed by the laws of your jurisdiction
          and heard by competent courts in your jurisdiction.
        </Text>
        <Text style={styles.paragraph}>
          Section 17 (MISCELLANEOUS): The subsection titled “Export Restriction” is deleted and replaced
          with the following: You may not use or otherwise export or re-export the Products, Services or
          related technology or any content contained therein, except as authorized by export control
          and sanctions laws of Canada, the United States and any other government having jurisdiction.
        </Text>
        <Text style={styles.subheading}>COLOMBIA</Text>
        <Text style={styles.paragraph}>
          Section 5 (FEEDBACK AND IDEAS): The last sentence of this section is deleted and replaced with
          the following: However, any Feedback you send us is provided on a non-confidential basis and
          you grant SFTC and its subsidiaries and affiliates an indefinite, worldwide authorization to
          use such Feedback for any purpose, commercial or otherwise, without notice, compensation or
          acknowledgement to you.
        </Text>
        <Text style={styles.subheading}>HONG KONG</Text>
        <Text style={styles.paragraph}>
          SFTC, Inc., an entity registered in the State of Oregon, USA and with its address at One SFTC
          Drive, Beaverton, OR 97005, USA) is: (1) the operator and manager of the SFTC apps in Hong
          Kong, and (2) our contracting entity for these Terms with you.
        </Text>
        <Text style={styles.paragraph}>
          Section 4 (USER CONTENT): The subsection titled “Right to User Content” is deleted and
          replaced with the following: You represent and warrant that your User Content, and our use of
          such User Content as permitted by these Terms, will not violate any laws of Hong Kong, rights
          of any person or entity, including any third-party rights, or cause injury to any person or
          entity. SFTC reserves the right to remove any User Content which in its sole opinion, violates
          or may violate the Hong Kong laws, rights of any person or entity, including any third-party
          rights, or causes or may cause injury to any person or entity. SFTC’s determination is final.
        </Text>
        <Text style={styles.subheading}>INDONESIA</Text>
        <Text style={styles.paragraph}>
          Section 14 (MODIFICATION AND TERMINATION): This section is modified to add the following
          paragraph at the end of the section: You agree to waive the provision of Article 1266 of the
          Indonesian Civil Code, to the extent that a prior court order is required to terminate these
          Terms with you and/or restrict your use of all or any part of the Services.
        </Text>
        <Text style={styles.paragraph}>
          Section 17 (MISCELLANEOUS): Language. These Terms are made in both the English language and
          the Indonesian language. Both texts are equally valid. In case of any inconsistency or
          different interpretation between the English text and the Indonesian text, the English text
          shall be the prevailing language.
        </Text>
        <Text style={styles.subheading}>JAPAN</Text>
        <Text style={styles.paragraph}>
          Section 1 (TERMS APPLICABLE TO YOU): The subsection titled “Updates” is deleted and replaced
          with the following: We may update these Terms from time to time. The “date of last revision”
          above indicates when these Terms were last updated. If we make updates, we may also send you a
          notification. Unless we indicate otherwise, updated Terms will be effective after posting in
          accordance with applicable law and your continued use of the Services, purchase of additional
          Products, or participation in Experiences will confirm your acceptance of the updates.
        </Text>
        <Text style={styles.paragraph}>
          Section 13 (LIMITATION OF LIABILITY): This section is deleted and replaced with the
          following: TO THE FULLEST EXTENT PERMITTED BY APPLICABLE LAW, NEITHER SFTC NOR ANY OF THE SFTC
          PARTIES WILL BE LIABLE TO YOU UNDER ANY THEORY OF LIABILITY, WHETHER BASED IN CONTRACT, TORT,
          NEGLIGENCE, STRICT LIABILITY, WARRANTY, STATUTE, OR OTHERWISE, FOR ANY SPECIAL, INCIDENTAL,
          INDIRECT, EXEMPLARY OR CONSEQUENTIAL DAMAGES.
        </Text>
        <Text style={styles.paragraph}>
          Section 16 (DISPUTES, JURISDICTION, VENUE): This section is deleted and replaced with the
          following: Applicable Law: Any disputes, claims, controversies, or legal proceedings arising
          out of or relating to these Terms, the Products, Services, or Experiences will be governed by
          and in all respects construed and enforced in accordance with Japanese law. Venue: Except
          where prohibited by applicable law, all Claims shall be resolved individually and
          exclusively in the state or federal courts located in Tokyo, Japan. Time to Bring a Claim: To
          the extent permitted by law, a Claim must be brought within one (1) year after the Claim
          arises.
        </Text>
        <Text style={styles.subheading}>PHILIPPINES</Text>
        <Text style={styles.paragraph}>
          Section 4 (USER CONTENT): The subsection titled “Content You Submit” is revised to add the
          following: You represent that you have the right to post your User Content, and you agree to
          execute all relevant documents to grant SFTC a non-exclusive, perpetual, transferable,
          sub-licensable, royalty-free, worldwide license to use any of the User Content that you post
          on or in connection with the Services, including the likeness of any person that appears in
          the User Content. SFTC may, in its sole discretion, remove any User Content at any time.
        </Text>
        <Text style={styles.paragraph}>
          Section 13 (LIMITATION OF LIABILITY): Subsection (1) of this section is deleted and replaced
          with the following: To the extent allowed under applicable law, none of the SFTC Parties will
          be liable for any special, incidental or consequential damages, including without limitation
          for any lost profits or lost data, that result from the use of or the inability to use the
          Services, the Products, conduct of other users of the Services (whether online or offline),
          attendance at an Experience, or any User Content or any other activity in connection with the
          use of the Services, even if SFTC has been advised of the possibility of such damages.
        </Text>
        <Text style={styles.subheading}>THAILAND</Text>
        <Text style={styles.paragraph}>
          Section 6 (USER CODE OF CONDUCT): This section is modified to add the following paragraph at
          the end of the section: SFTC has adopted a policy of removing or disabling access to illegal
          Content upon proper notice.
        </Text>
        <Text style={styles.paragraph}>
          Section 7 (COPYRIGHT INFRINGEMENT): This section is deleted and replaced with the following:
          SFTC has adopted a policy of terminating, in appropriate circumstances, the accounts of users
          found to infringe the intellectual property rights of others.
        </Text>
        <Text style={styles.subheading}>VIETNAM</Text>
        <Text style={styles.paragraph}>
          Section 4 (USER CONTENT): The second paragraph in the subsection titled “License to Use” is
          deleted and replaced with the following: You hereby irrevocably waive any inalienable “moral
          rights” or other rights with respect to attribution of authorship or integrity of materials
          regarding your User Content that you may have under any applicable law or under any legal
          theory.
        </Text>
        <Text style={styles.paragraph}>
          Section 7 (COPYRIGHT INFRINGEMENT): The first paragraph in this section is deleted and
          replaced with the following: SFTC has adopted a policy of terminating, in appropriate
          circumstances, the accounts of users found to infringe the intellectual property rights of
          others.
        </Text>
        <Text style={styles.paragraph}>
          Section 17 (MISCELLANEOUS): Language. These Terms are made in both the English and the
          Vietnamese. Both texts are equally valid. In case of any inconsistency or different
          interpretation between the English text and the Vietnamese text, the text that is interpreted
          more favorably to you will prevail.
        </Text>
        <Text style={styles.subheading}>EUROPEAN COUNTRIES</Text>
        <Text style={styles.paragraph}>
          The following revisions apply to all European countries, except for Austria, Belgium, France,
          Germany, Hungary, Italy, Netherlands, Poland, Spain, Switzerland, and the United Kingdom,
          where alternative and/or additional clauses apply.
        </Text>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  closeButton: {
    padding: 4,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#000000',
    marginBottom: 10,
    lineHeight: 36,
    letterSpacing: -0.3,
  },
  heading: {
    fontSize: 16,
    fontWeight: '700',
    color: '#000000',
    marginTop: 16,
    marginBottom: 6,
  },
  subheading: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000000',
    marginTop: 12,
    marginBottom: 4,
  },
  paragraph: {
    fontSize: 14,
    color: '#111111',
    lineHeight: 22,
    marginBottom: 10,
  },
  listItem: {
    fontSize: 14,
    color: '#111111',
    lineHeight: 22,
    marginBottom: 6,
  },
});
