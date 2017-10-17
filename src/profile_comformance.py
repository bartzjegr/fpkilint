from cert_helpers import *
import json
import datetime
import pytz
import sys
import ast

class config_entry:
    def __init__(self):
        self.value = ""
        self.oid = ""


def lint_other_extensions(cfg_opt, cert, cfg_sect, outJson):
    #Todo: requirement?
    #'1.3.6.1.5.5.7.1.24': 'tls_feature',
    #'1.2.840.113533.7.65.0': 'entrust_version_extension',
    #'2.16.840.1.113730.1.1': 'netscape_certificate_type',
    # https://tools.ietf.org/html/rfc6962.html#page-14
    #'1.3.6.1.4.1.11129.2.4.2': 'signed_certificate_timestamp_list',

    return

def lint_policy_mappings(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    content = False
    oids = []
    c_policies = None
    for e in extensions:
        if e['extn_id'] == 'policy_mappings':
            c_policies = e
            break

    for ce in cfg_opt:
        if ce == "policy_mappings_present":
            output(not c_policies == None, ce, cfg_opt, cfg_sect, e['extn_id'], outJson)
        elif ce == "policy_mappings_is_critical":
            if not c_policies == None:
               output(c_policies['critical'], ce, cfg_opt, cfg_sect, str(c_policies['critical']), outJson)
        elif ce == "policy_mappings_content":
            if not c_policies == None:
              for item in c_policies['extn_value']:
                oids += [item['policy_identifier']]
              if [cfg_opt[ce].oid] <= oids:
                content = True
              output(content, ce, cfg_opt, cfg_sect, str(oids), outJson)
        else:
            missing(ce, cfg_opt, cfg_sect, outJson)
    return


def lint_name_constraints(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False

    for e in extensions: #not in cert, mimicing aia
        if e['extn_id'].native == "name_constraints":
                found = True
                break

    output(found, "name_constraints_present", cfg_opt, cfg_sect, e['extn_id'].native, outJson)
    if found:
        output(e['critical'].native, "name_constraints_is_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson) #typo in template.json?

        #todo: other fields requirements

    else:
        missing("name_constraints_is_critical", cfg_opt, cfg_sect, outJson)

    return


def lint_piv_naci(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False

    for e in extensions:
        if e['extn_id'] == cfg_opt["piv_naci_present"].oid:
                found = True
                break
        output(found, "piv_naci_present", cfg_opt, cfg_sect, e['extn_id'], outJson)
    if found:
        output(e['critical'].native, "piv_naci_is_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson) #typo in template.json?
    else:
        missing("piv_naci_is_critical", cfg_opt, cfg_sect, outJson)
    return


def lint_validity(cfg_opt, cert, cfg_sect, outJson):
    nb = cert['tbs_certificate']['validity']['not_before']
    na = cert['tbs_certificate']['validity']['not_after']
    lifespan = na.native - nb.native

    cut_off = datetime.datetime(2050, 1, 1)
    cut_off = cut_off.replace(tzinfo=pytz.UTC)

    if nb.name == 'utc_time':
        if nb.native > cut_off:
            print("notBefore is required to be GeneralizedTime")

    for ce in cfg_opt:
        if ce == "validity_period_maximum":
            result = lifespan.days < int(cfg_opt[ce].value) or int(cfg_opt[ce].value) == 0
            cert_value = lifespan.days
        elif ce == "validity_period_generalized_time":
            result = nb.native < cut_off
            cert_value = nb.native
        output(result, ce, cfg_opt, cfg_sect, cert_value, outJson)
    return


def lint_subject(cfg_opt, cert, cfg_sect, outJson):
    subject = cert['tbs_certificate']['subject']
    found_base_dn = False
    found = False
    # iterate over all rdn entries
    for ce in cfg_opt:
        if "rdn_" in ce:
            # print(ce + " " + cfg_opt[ce].oid)
            rdn_seq = subject.chosen
            for rdn in rdn_seq:
                for name in rdn:
                    if name['type'].dotted == cfg_opt[ce].oid:
                        found = True
                        break
            output(found, ce, cfg_opt, cfg_sect, name['type'].dotted, outJson)
        elif "subject_base_dn" in ce:
            for rdn in subject.native: # need oid for base_dn to search for oid
                if 'base_dn' in rdn:
                    found_base_dn = True
                    break
            output(found_base_dn, ce, cfg_opt, cfg_sect, str(rdn), outJson)

    return


def lint_key_usage(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False

    for e in extensions:
        if e['extn_id'].native == "key_usage":
                found = True
                break

    output(found, "key_usage_present", cfg_opt, cfg_sect, e['extn_id'].native, outJson)
    if found:
        output(e['critical'].native, "key_usage_is_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson)
        output('digital_signature' in e['extn_value'].native, "key_usage_digitalSignature", cfg_opt, cfg_sect, str(e['extn_value'].native), outJson)
        output('non_repudiation' in e['extn_value'].native, "key_usage_nonRepudiation", cfg_opt, cfg_sect, str(e['extn_value'].native), outJson)
        output('key_encipherment' in e['extn_value'].native, "key_usage_keyEncipherment", cfg_opt, cfg_sect, str(e['extn_value'].native), outJson)
        output('data_encipherment' in e['extn_value'].native, "key_usage_dataEncipherment", cfg_opt, cfg_sect, str(e['extn_value'].native), outJson)
        output('key_agreement' in e['extn_value'].native, "key_usage_keyAgreement", cfg_opt, cfg_sect,e['extn_value'].native, outJson)
        output('key_cert_sign' in e['extn_value'].native, "key_usage_keyCertSign", cfg_opt, cfg_sect, str(e['extn_value'].native), outJson)
        output('crl_sign' in e['extn_value'].native, "key_usage_cRLSign", cfg_opt, cfg_sect, str(e['extn_value'].native), outJson)
        output('encipher_only' in e['extn_value'].native, "key_usage_encipherOnly", cfg_opt, cfg_sect, str(e['extn_value'].native), outJson)
        output('decipher_only' in e['extn_value'].native, "key_usage_decipherOnly", cfg_opt, cfg_sect, str(e['extn_value'].native), outJson)
    else:
        missing("key_usage_is_critical", cfg_opt, cfg_sect, outJson)
        missing("key_usage_digitalSignature", cfg_opt, cfg_sect, outJson)
        missing("key_usage_nonRepudiation", cfg_opt, cfg_sect, outJson)
        missing("key_usage_keyEncipherment", cfg_opt, cfg_sect, outJson)
        missing("key_usage_dataEncipherment", cfg_opt, cfg_sect, outJson)
        missing("key_usage_keyAgreement", cfg_opt, cfg_sect, outJson)
        missing("key_usage_keyCertSign", cfg_opt, cfg_sect, outJson)
        missing("key_usage_cRLSign", cfg_opt, cfg_sect, outJson)
        missing("key_usage_encipherOnly", cfg_opt, cfg_sect, outJson)
        missing("key_usage_decipherOnly", cfg_opt, cfg_sect, outJson)
    return


def lint_issuer(cfg_opt, cert, cfg_sect, outJson):
    cert_leaf = cert['tbs_certificate']['issuer']
    found_base_dn = False
    found = False
    # iterate over all rdn entries
    for ce in cfg_opt:
        if "rdn_" in ce:
            # print(ce + " " + cfg_opt[ce].oid)
            rdn_seq = cert_leaf.chosen
            for rdn in rdn_seq:
                for name in rdn:
                    if name['type'].dotted == cfg_opt[ce].oid:
                        found = True
                        break
            output(found, ce, cfg_opt, cfg_sect, name['type'].dotted, outJson)
        elif "subject_base_dn" in ce:
            for rdn in cert_leaf.native: # need oid for base_dn to search for oid
                if 'base_dn' in rdn:
                    found_base_dn = True
                    break
            output(found_base_dn, ce, cfg_opt, cfg_sect, "base_dn missing", outJson)
    return


def lint_akid(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False
    #cert entry not found

    for e in extensions:
        if e['extn_id'].native == "key_identifier":
                found = True
                break

    output(found, "akid_present", cfg_opt, cfg_sect, str(e['extn_id'].native), outJson)
    if found:
        output(e['critical'].native, "akid_is_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson)
        #TODO: output(e['require_method_one'], "akid_require_method_one", cfg_opt, cfg_sect, str(e['critical'].native), outJson)
    else:
        missing("akid_is_critical", cfg_opt, cfg_sect, outJson)
        #TODO: missing("akid_require_method_one", cfg_opt, cfg_sect, outJson)
    return

def lint_skid(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False
    #cert entry not found

    for e in extensions:
        if e['extn_id'].native == "key_identifier":
                found = True
                break

    output(found, "skid_present", cfg_opt, cfg_sect, e['extn_id'].native, outJson)
    if found:
        output(e['critical'].native, "skid_is_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson)
        #TODO: output(e['require_method_one'], "skid_require_method_one", cfg_opt, cfg_sect, str(e['critical'].native), outJson)
    else:
        missing("skid_is_critical", cfg_opt, cfg_sect, outJson)
        #TODO: missing("skid_require_method_one", cfg_opt, cfg_sect, outJson)

    return

def lint_policy_constraints(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False

    for e in extensions: #not in cert, mimicing aia
        if e['extn_id'].native == "policy_constraints":
                found = True
                break

    output(found, "policy_constraints_present", cfg_opt, cfg_sect, e['extn_id'].native, outJson)
    if found:
        output(e['critical'].native, "policy_constraints_is_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson) #typo in template.json?

        #todo: requirement for other fields

    else:
        missing("policy_constraints_is_critical", cfg_opt, cfg_sect, outJson)
    return


def lint_serial_number(cfg_opt, cert, cfg_sect, outJson):
    cert_leaf = cert['tbs_certificate']['serial_number'].native
    ln = len(str(cert_leaf))
    output(ln > int(cfg_opt["serial_min_length"].value),  "serial_min_length", cfg_opt, cfg_sect, str(cert_leaf), outJson)
    output(ln < int(cfg_opt["serial_max_length"].value), "serial_max_length", cfg_opt, cfg_sect, str(cert_leaf), outJson)
    return


def lint_basic_constraints(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False

    for e in extensions: #not in cert, mimicing aia
        if e['extn_id'].native == "basic_constraints":
                found = True
                break

    output(found, "basic_constraints_present", cfg_opt, cfg_sect, e['extn_id'].native, outJson)
    if found:
        output(e['critical'].native, "basic_constraints_is_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson) #typo in template.json?

        #todo: other fields requirements

    else:
        missing("basic_constraints_is_critical", cfg_opt, cfg_sect, outJson)

    return


def lint_cert_policies(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    content = False
    oids = []
    c_policies = None
    for e in extensions:
        if e['extn_id'] == 'certificate_policies':
            c_policies = e
            break

    for ce in cfg_opt:
        if ce == "certificate_policies_present":
            output(not c_policies == None, ce, cfg_opt, cfg_sect, e['extn_id'], outJson)
        elif ce == "certificate_policies_is_critical":
            if not c_policies == None:
               output(c_policies['critical'] == True, ce, cfg_opt, cfg_sect, str(c_policies['critical']), outJson)
            else:
                missing(ce, cfg_opt, cfg_sect, outJson)
        elif ce == "certificate_policies_content":
            if not c_policies == None:
              for item in c_policies['extn_value']:
                oids += [item['policy_identifier']]
              if [cfg_opt[ce].oid] <= oids:
                content = True
              output(content, ce, cfg_opt, cfg_sect, str(oids), outJson)
            else:
              missing(ce, cfg_opt, cfg_sect, outJson)
    return


def lint_subject_public_key_info(cfg_opt, cert, cfg_sect, outJson):
    cert_leaf = cert['tbs_certificate']['subject_public_key_info']
    algo = cert_leaf['algorithm']['algorithm'].dotted
    found = False
    for ce in cfg_opt:
        if cfg_opt[ce].oid == algo:
            found = True
            break
    output(found, ce, cfg_opt, cfg_sect, algo, outJson)
    blen = cert_leaf['public_key'].native['modulus'].bit_length()

    output(blen > int(cfg_opt['subject_public_key_min_size'].value), 'subject_public_key_min_size',
           cfg_opt, cfg_sect, str(blen), outJson)
    output(blen < int(cfg_opt['subject_public_key_max_size'].value), 'subject_public_key_max_size',
           cfg_opt, cfg_sect, str(blen), outJson)
    return


def lint_aia(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False

    for e in extensions:
        if e['extn_id'].native == "authority_information_access":
                found = True
                break

    output(found, "aia_present", cfg_opt, cfg_sect, e['extn_id'].native, outJson)
    if found:
        output(e['critical'].native, "aia_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson) #typo in template.json?
        ca_issuers_present = False
        ocsp_present = False
        for item in e['extn_value'].native:
            if item['access_method'] == 'ca_issuers':
                ca_issuers_present = True #search oid?
            elif item['access_method'] == 'ocsp':
                ocsp_present = True
        output(ca_issuers_present, "aia_ca_issuers_present", cfg_opt, cfg_sect, item['access_method'], outJson)
        output(ocsp_present, "aia_ocsp_present", cfg_opt, cfg_sect, item['access_method'], outJson)
        #todo: requirements for other field

    else:
        missing("aia_critical", cfg_opt, cfg_sect, outJson)
        missing("aia_ca_issuers_present", cfg_opt, cfg_sect, outJson)
        missing("aia_ocsp_present", cfg_opt, cfg_sect, outJson)
    return


def lint_san(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False

    for e in extensions:
        if e['extn_id'].native == "subject_alt_name":
                found = True
                break

    output(found, "san_present", cfg_opt, cfg_sect, e['extn_id'].native, outJson)
    if found:
        output(e['critical'].native, "san_is_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson)
        c_oid = e['extn_value'].native[0]['type_id']
        output(c_oid == cfg_opt['san_rfc822_name'].oid, "san_rfc822_name", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['san_x400_address'].oid, "san_x400_address", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['san_directory_name'].oid, "san_directory_name", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['san_edi_party_name'].oid, "san_edi_party_name", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['san_uniform_resource_identifier'].oid, "san_uniform_resource_identifier", cfg_opt, cfg_sect,c_oid, outJson)
        output(c_oid == cfg_opt['san_ip_address'].oid, "san_ip_address", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['san_registered_id'].oid, "san_registered_id", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['san_other_name_upn'].oid, "san_other_name_upn", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['san_other_name_piv_fasc_n'].oid, "san_other_name_piv_fasc_n", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['san_uniform_resource_identifier_chuid'].oid, "san_uniform_resource_identifier_chuid", cfg_opt, cfg_sect, c_oid, outJson)
    else:
        missing("san_is_critical", cfg_opt, cfg_sect, outJson)
        missing("san_rfc822_name", cfg_opt, cfg_sect, outJson)
        missing("san_x400_address", cfg_opt, cfg_sect, outJson)
        missing("san_directory_name", cfg_opt, cfg_sect, outJson)
        missing("san_edi_party_name", cfg_opt, cfg_sect, outJson)
        missing("san_uniform_resource_identifier", cfg_opt, cfg_sect, outJson)
        missing("san_ip_address", cfg_opt, cfg_sect, outJson)
        missing("san_registered_id", cfg_opt, cfg_sect, outJson)
        missing("san_other_name_upn", cfg_opt, cfg_sect, outJson)
        missing("san_other_name_piv_fasc_n", cfg_opt, cfg_sect, outJson)
        missing("san_uniform_resource_identifier_chuid", cfg_opt, cfg_sect, outJson)

    return


def lint_ian(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False

    for e in extensions:
        if e['extn_id'].native == "issuer_alt_name":
                found = True
                break

    output(found, "ian_present", cfg_opt, cfg_sect, e['extn_id'].native, outJson)
    if found:
        output(e['critical'].native, "ian_is_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson)
        c_oid = e['extn_value'].native[0]['type_id']
        output(c_oid == cfg_opt['ian_other_name'].oid, "ian_other_name", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['ian_rfc822_name'].oid, "ian_rfc822_name", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['ian_dns_name'].oid, "ian_dns_name", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['ian_x400_address'].oid, "ian_x400_address", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['ian_directory_name'].oid, "ian_directory_name", cfg_opt, cfg_sect,c_oid, outJson)
        output(c_oid == cfg_opt['ian_edi_party_name'].oid, "ian_edi_party_name", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['ian_uniform_resource_identifier'].oid, "ian_uniform_resource_identifier", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['ian_ip_address'].oid, "ian_ip_address", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['ian_other_name_upn'].oid, "ian_other_name_upn", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['ian_other_name_piv_fasc_n'].oid, "ian_other_name_piv_fasc_n", cfg_opt, cfg_sect, c_oid, outJson)
        output(c_oid == cfg_opt['ian_uniform_resource_identifier_chuid'].oid, "ian_uniform_resource_identifier_chuid", cfg_opt, cfg_sect, c_oid, outJson)

    else:
        missing("ian_is_critical", cfg_opt, cfg_sect, outJson)
        missing("ian_other_name", cfg_opt, cfg_sect, outJson)
        missing("ian_rfc822_name", cfg_opt, cfg_sect, outJson)
        missing("ian_dns_name", cfg_opt, cfg_sect, outJson)
        missing("ian_x400_address", cfg_opt, cfg_sect, outJson)
        missing("ian_directory_name", cfg_opt, cfg_sect, outJson)
        missing("ian_edi_party_name", cfg_opt, cfg_sect, outJson)
        missing("ian_uniform_resource_identifier", cfg_opt, cfg_sect, outJson)
        missing("ian_ip_address", cfg_opt, cfg_sect, outJson)
        missing("ian_other_name_upn", cfg_opt, cfg_sect, outJson)
        missing("ian_other_name_piv_fasc_n", cfg_opt, cfg_sect, outJson)
        missing("ian_uniform_resource_identifier_chuid", cfg_opt, cfg_sect, outJson)

    return


def lint_eku(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False

    for e in extensions:
        if e['extn_id'].native == "extended_key_usage":
                found = True
                break

    output(found, "eku_present", cfg_opt, cfg_sect, e['extn_id'].native, outJson)
    if found:
        output(e['critical'].native, "eku_is_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_server_auth'].oid, "eku_oid_server_auth", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_client_auth'].oid, "eku_oid_client_auth", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_code_signing'].oid, "eku_oid_code_signing", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_email_protection'].oid, "eku_oid_email_protection", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_time_stamping'].oid, "eku_oid_time_stamping", cfg_opt, cfg_sect,e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_ocsp_signing'].oid, "eku_oid_ocsp_signing", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_any_eku'].oid, "eku_oid_any_eku", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_smart_card_logon'].oid, "eku_oid_smart_card_logon", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_ipsec_ike_intermediate'].oid, "eku_oid_ipsec_ike_intermediate", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_ipsec_end_system'].oid, "eku_oid_ipsec_end_system", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_ipsec_tunnel_termination'].oid, "eku_oid_ipsec_tunnel_termination", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_ipsec_user'].oid, "eku_oid_ipsec_user", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_piv_card_auth'].oid, "eku_oid_piv_card_auth", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_pivi_content_signing'].oid, "eku_oid_pivi_content_signing", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_smartCardLogon'].oid, "eku_oid_smartCardLogon", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_pkinit_KPKdc'].oid, "eku_oid_pkinit_KPKdc", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_oid_pkinit_KPClientAuth'].oid, "eku_oid_pkinit_KPClientAuth", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)
        output(e['extn_value'].native[0] == cfg_opt['eku_other'].oid, "eku_other", cfg_opt, cfg_sect, e['extn_value'].native[0], outJson)

    else:
        missing("eku_is_critical", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_server_auth", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_client_auth", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_code_signing", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_email_protection", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_time_stamping", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_ocsp_signing", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_any_eku", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_smart_card_logon", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_ipsec_ike_intermediate", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_ipsec_end_system", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_ipsec_tunnel_termination", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_ipsec_user", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_piv_card_auth", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_pivi_content_signing", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_smartCardLogon", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_pkinit_KPKdc", cfg_opt, cfg_sect, outJson)
        missing("eku_oid_pkinit_KPClientAuth", cfg_opt, cfg_sect, outJson)
        missing("eku_other", cfg_opt, cfg_sect, outJson)
    return


def lint_crldp(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False

    for e in extensions:
        if e['extn_id'].native == "crl_distribution_points":
                found = True
                break

    output(found, "crldp_present", cfg_opt, cfg_sect, e['extn_id'].native, outJson)
    if found:
        output(e['critical'].native, "crldp_is_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson) #typo in template.json?
        crldp_http = False
        crldp_ldap = False
        for item in e['extn_value'].native:
            if "http" in item['distribution_point']:
                crldp_http = True #search oid?
            elif "ldap" in item['distribution_point']:
                crldp_ldap = True
        output(crldp_http, "crldp_http", cfg_opt, cfg_sect, str(item['distribution_point'][0]), outJson)
        output(crldp_ldap, "crldp_ldap", cfg_opt, cfg_sect, str(item['distribution_point'][0]), outJson)
        #todo: requirements for other fields

    else:
        missing("crldp_is_critical", cfg_opt, cfg_sect, outJson)
        missing("crldp_http", cfg_opt, cfg_sect, outJson)
        missing("crldp_ldap", cfg_opt, cfg_sect, outJson)
    return


def lint_sia(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False

    for e in extensions: #not in cert, mimicing aia
        if e['extn_id'].native == "subject_information_access":
                found = True
                break

    output(found, "sia_present", cfg_opt, cfg_sect, e['extn_id'].native, outJson)
    if found:
        output(e['critical'].native, "sia_is_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson)

        # todo: requirements for other fields

    else:
        missing("sia_is_critical", cfg_opt, cfg_sect, outJson)

    return


def lint_pkup(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False

    for e in extensions: #not in cert, mimicing aia
        if e['extn_id'].native == "private_key_usage_period":
                found = True
                break

    output(found, "pkup_present", cfg_opt, cfg_sect, e['extn_id'].native, outJson)
    if found:
        output(e['critical'].native, "pkup_is_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson) #typo in template.json?

    else:
        missing("pkup_is_critical", cfg_opt, cfg_sect, outJson)
    return


def lint_sub_dir_attr(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False

    for e in extensions: #not in cert, mimicing aia
        if e['extn_id'].native == "subject_directory_attribute":
                found = True
                break

    output(found, "subject_directory_attributes_present", cfg_opt, cfg_sect, e['extn_id'].native, outJson)
    if found:
        output(e['critical'].native, "subject_directory_attributes_is_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson) #typo in template.json?

    else:
        missing("subject_directory_attributes_is_critical", cfg_opt, cfg_sect, outJson)
    return


def lint_signature_algorithm(cfg_opt, cert, cfg_sect, outJson):
    cert_leaf = cert['signature_algorithm']['algorithm']
    oid = cert_leaf.dotted
    found = False
    for ce in cfg_opt:
        if cfg_opt[ce].oid == oid:
            found = True


    cert_leaf1 = cert['tbs_certificate']['signature']['algorithm'].dotted
    if not cert_leaf.dotted == cert_leaf1:
        print ("['signature_algorithm']['signature'] and ['tbs_certificate']['signature']['algorithm'] has differnt values: "
            + str(cert_leaf.dotted) + " vs. " + str(cert_leaf1))
    output(found and cert_leaf.dotted == cert_leaf1, ce, cfg_opt, cfg_sect, cert_leaf.dotted, outJson)
    return


def lint_version(cfg_opt, cert, cfg_sect, outJson):
    cert_leaf = cert['tbs_certificate']['version'].native

    output(int(cert_leaf[1:]) > int(cfg_opt['minimum_version'].value), "minimum_version", cfg_opt, cfg_sect, cert_leaf, outJson)
    return


def lint_ocsp_nocheck(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False

    for e in extensions: #not in cert, mimicing aia
        if e['extn_id'].native == "ocsp_no_ckeck":
                found = True
                break

    output(found, "ocsp_no_check_present", cfg_opt, cfg_sect, e['extn_id'].native, outJson)
    if found:
        output(e['critical'].native, "ocsp_no_check_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson) #typo in template.json?

    else:
        missing("ocsp_no_check_critical", cfg_opt, cfg_sect, outJson)
    return


def lint_inhibit_any(cfg_opt, cert, cfg_sect, outJson):
    extensions = cert['tbs_certificate']['extensions']
    found = False
    critical = False

    for e in extensions: #not in cert, mimicing aia
        if e['extn_id'].native == "inhibit_any_policy":
                found = True
                break

    output(found, "inhibit_any_policy_present", cfg_opt, cfg_sect, e['extn_id'].native, outJson)
    if found:
        output(e['critical'].native, "inhibit_any_policy_is_critical", cfg_opt, cfg_sect, str(e['critical'].native), outJson) #typo in template.json?

    else:
        missing("inhibit_any_policy_is_critical", cfg_opt, cfg_sect, outJson)
    return

def output(result, ce, cfg_opt, cfg_sect, cert_value, outJson):
    if result is True and cfg_opt[ce].value is '1' or result is False and cfg_opt[ce].value is '2':
      dictn = ast.literal_eval('{"Section": "' + cfg_sect + '",' +
                      '"Item": "' + ce + '",' +
                      '"Value": "' + cfg_opt[ce].value + '",' +
                      '"OID": "' + cfg_opt[ce].oid + '",' +
                      '"OUTPUT": "FAIL with Cert Value: ' + str(cert_value) + '"}')
    else:
      dictn = ast.literal_eval('{"Section": "' + cfg_sect + '",' +
                      '"Item": "' + ce + '",' +
                      '"Value": "' + cfg_opt[ce].value + '",' +
                      '"OID": "' + cfg_opt[ce].oid + '",' +
                      '"OUTPUT": "PASS with Cert Value: ' + str(cert_value) + '"}')
    outJson.append(dictn.copy())
    return
def missing(ce, cfg_opt, cfg_sect, outJson):
    dictn = ast.literal_eval('{"Section": "' + cfg_sect + '",' +
                   '"Item": "' + ce + '",' +
                   '"Value": "' + cfg_opt[ce].value + '",' +
                   '"OID": "' + cfg_opt[ce].oid + '",' +
                   '"OUTPUT": "MISSING Cert Value"}')
    outJson.append(dictn.copy())
    return

conformance_check_functions = {
    'Other Extensions': lint_other_extensions,
    'Policy Mappings': lint_policy_mappings,
    'Name Constraints': lint_name_constraints,
    'PIV NACI': lint_piv_naci,
    'Validity': lint_validity,
    'Subject': lint_subject,
    'Issuer': lint_issuer,
    'Authority Key Identifier': lint_akid,
    'Subject Key Identifier': lint_skid,
    'Key Usage': lint_key_usage,
    'Policy Constraints': lint_policy_constraints,
    'Serial Number': lint_serial_number,
    'Basic Constraints': lint_basic_constraints,
    'Certificate Policies': lint_cert_policies,
    'subjectPublicKeyInfo': lint_subject_public_key_info,
    'Authority Information Access': lint_aia,
    'Subject Alternative Name': lint_san,
    'Issuer Alternative Name': lint_ian,
    'Extended Key Usage': lint_eku,
    'CRL Distribution Point': lint_crldp,
    'Subject Information Access': lint_sia,
    'Private Key Usage Period': lint_pkup,
    'Subject Directory Attributes': lint_sub_dir_attr,
    'Signature Algorithm': lint_signature_algorithm,
    'Version': lint_version,
    'OCSP No-Check': lint_ocsp_nocheck,
    'Inhibit Any Policy': lint_inhibit_any
    }


if __name__ == "__main__":

    filePath = "testcerts/test.cer"
    with open(filePath, 'rb') as cert_file:
        encoded = cert_file.read()

    input_cert = None

    try:
        input_cert = parse_cert(encoded)
    except:
        # todo add proper exception handlers
        print("Failed to parse the certificate")

    if input_cert is None:
        exit(0)

    print("\nSubject:\n{}\n".format(get_pretty_dn(input_cert.subject, "\n", "=")))
    print("Issuer:\n{}\n".format(get_pretty_dn(input_cert.issuer, "\n", "=")))

    with open('profiles/template.json') as json_data:
        json_profile = json.load(json_data)

    cert_profile = {}

    for entry in json_profile:
        if entry['Section'] not in cert_profile:
            cert_profile[entry['Section']] = {}
        pce = config_entry()
        pce.value = entry['Value']
        pce.oid = entry['OID']
        cert_profile[entry['Section']][entry['Item']] = pce
    outJson = []
    for cfg_sect in cert_profile:
        # print(cfg_sect)
        if cfg_sect in conformance_check_functions:
            conformance_check_functions[cfg_sect](cert_profile[cfg_sect], input_cert, cfg_sect, outJson)
        else:
            print("Invalid config section:  {}".format(cfg_sect))
        json.dump(outJson, sys.stdout, indent=2)

