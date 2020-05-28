package br.leg.go.jatai.portal.plugin.sign;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintStream;
import java.nio.file.Files;
import java.security.GeneralSecurityException;
import java.security.KeyStore;
import java.security.PrivateKey;
import java.security.Security;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.List;
import java.util.TimeZone;

import javax.imageio.ImageIO;
import javax.swing.border.StrokeBorder;

import java.security.cert.CRL;
import java.security.cert.Certificate;
import java.security.cert.CertificateExpiredException;
import java.security.cert.CertificateFactory;
import java.security.cert.CertificateNotYetValidException;
import java.security.cert.X509CRL;
import java.security.cert.X509Certificate;
import java.text.SimpleDateFormat;

import org.bouncycastle.cert.ocsp.BasicOCSPResp;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.tsp.TimeStampToken;

import com.itextpdf.forms.PdfAcroForm;
import com.itextpdf.io.image.ImageDataFactory;
import com.itextpdf.io.source.ByteArrayOutputStream;
import com.itextpdf.kernel.geom.Rectangle;
import com.itextpdf.kernel.pdf.PdfDictionary;
import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfName;
import com.itextpdf.kernel.pdf.PdfReader;
import com.itextpdf.kernel.pdf.PdfString;
import com.itextpdf.kernel.pdf.StampingProperties;
import com.itextpdf.kernel.pdf.annot.PdfStampAnnotation;
import com.itextpdf.kernel.pdf.annot.PdfWidgetAnnotation;
import com.itextpdf.signatures.BouncyCastleDigest;
import com.itextpdf.signatures.CRLVerifier;
import com.itextpdf.signatures.CertificateInfo;
import com.itextpdf.signatures.CertificateVerification;
import com.itextpdf.signatures.DigestAlgorithms;
import com.itextpdf.signatures.IExternalDigest;
import com.itextpdf.signatures.OCSPVerifier;
import com.itextpdf.signatures.PdfPKCS7;
import com.itextpdf.signatures.PdfSignatureAppearance;
import com.itextpdf.signatures.PdfSigner;
import com.itextpdf.signatures.PrivateKeySignature;
import com.itextpdf.signatures.SignaturePermissions;
import com.itextpdf.signatures.SignatureUtil;
import com.itextpdf.signatures.VerificationException;
import com.itextpdf.signatures.VerificationOK;

public class PlugSignPortalCMJ  {
	
	BouncyCastleProvider provider = null;
	String[] args = null;
	
    public static void main(String[] args) {

    	BouncyCastleProvider provider = new BouncyCastleProvider();
        Security.addProvider(provider);
        
        PlugSignPortalCMJ app = new PlugSignPortalCMJ();
        app.provider = provider;
        app.args = args;
    	switch (args[0]) {
		case "cert_protocolo":
			try {
				app.certProtocolo();
			} catch (Exception e) {
				return ;
			}
		default:
			break;
		}
    	return ;   	
    	
    }

    public boolean isSigned(String path) throws IOException, GeneralSecurityException {
    	PdfDocument pdfDoc = new PdfDocument(new PdfReader(path));
    	return this.isSigned(pdfDoc);
    }
    public boolean isSigned(PdfDocument pdfDoc) throws IOException, GeneralSecurityException {
        PdfAcroForm form = PdfAcroForm.getAcroForm(pdfDoc, false);
        SignaturePermissions perms = null;
        SignatureUtil signUtil = new SignatureUtil(pdfDoc);
        List<String> names = signUtil.getSignatureNames();
        return !names.isEmpty();
    }

    public Object[] getImageFullSign() throws IOException {

        ByteArrayOutputStream bOut = new ByteArrayOutputStream();

        int w = 566; //566
        int h = 813; //813
        
        BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = img.createGraphics();
        //g.setBackground(new Color(255, 0, 0, 127));
        g.setColor(new Color(0, 76, 64, 200));
        g.setStroke(new BasicStroke(0));
        g.fillRect(0, 0, w, h);
        g.dispose();
        
        ImageIO.write(img, "png", bOut);
        
        Rectangle rectSign = new Rectangle(595-w+5-20, 842-h-15, w+1, h+1);
        Object[] r = new Object[2];
        r[0] = rectSign;
        r[1] = bOut.toByteArray();
        	
        return r;        
    }
    
    

    public Object[] getImageLeftSign() throws IOException {

        ByteArrayOutputStream bOut = new ByteArrayOutputStream();

        int w = 48; //566
        int h = 300; //813
        
        BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = img.createGraphics();
        //g.setRenderingHint(RenderingHints.KEY_FRACTIONALMETRICS,
        //	    RenderingHints.VALUE_FRACTIONALMETRICS_ON);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, 
        	    RenderingHints.VALUE_TEXT_ANTIALIAS_LCD_HBGR);
        g.setRenderingHint(RenderingHints.KEY_RENDERING, 
        	    RenderingHints.VALUE_RENDER_QUALITY);
		/*
		 * g.setRenderingHint( RenderingHints.KEY_TEXT_ANTIALIASING,
		 * RenderingHints.VALUE_TEXT_ANTIALIAS_ON); g.setRenderingHint(
		 * RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
		 */
        //g.setBackground(new Color(255, 0, 0, 127));
        g.setColor(new Color(0, 76, 64, 255));
        g.setStroke(new BasicStroke(0));
        g.fillRect(w/4, 0, w/2, h);

        g.setColor(new Color(255,255,255));
        Font font = new Font("Arial", Font.BOLD, 18);
        g.setFont(font);
        FontMetrics fm = g.getFontMetrics();
        int wfm = fm.stringWidth(this.args[6]);
        int hfm = fm.getHeight();
        g.rotate(Math.PI*1.5);
        g.drawString(this.args[6], -wfm/2-h/2, w/4+19);
        g.rotate((-1)*Math.PI*1.5);

        
        g.setColor(new Color(0,0,0));        
        font = new Font("Arial", Font.BOLD, 10);
        g.setFont(font);
        fm = g.getFontMetrics();
        wfm = fm.stringWidth(this.args[3]);
        hfm = fm.getHeight();
        g.rotate(Math.PI*1.5);
        g.drawString(this.args[3], -wfm, 10);
        g.rotate((-1)*Math.PI*1.5);
        
        g.rotate(Math.PI*1.5);
        g.drawString("Data: " + this.args[4] + " - Hora: " + this.args[5], -h, 10);

        
        g.dispose();
        
        ImageIO.write(img, "png", bOut);
        
        Rectangle rectSign = new Rectangle(15, 842-h-120, w+1, h+1);
        Object[] r = new Object[2];
        r[0] = rectSign;
        r[1] = bOut.toByteArray();
        	
        return r;        
    }

    public Object[] getImageRightSign() throws IOException {

        ByteArrayOutputStream bOut = new ByteArrayOutputStream();

        int w = 48; //566
        int h = 225; //813
        
        BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = img.createGraphics();
        //g.setRenderingHint(RenderingHints.KEY_FRACTIONALMETRICS,
        //	    RenderingHints.VALUE_FRACTIONALMETRICS_ON);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, 
        	    RenderingHints.VALUE_TEXT_ANTIALIAS_LCD_HBGR);
        g.setRenderingHint(RenderingHints.KEY_RENDERING, 
        	    RenderingHints.VALUE_RENDER_QUALITY);
		/*
		 * g.setRenderingHint( RenderingHints.KEY_TEXT_ANTIALIASING,
		 * RenderingHints.VALUE_TEXT_ANTIALIAS_ON); g.setRenderingHint(
		 * RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
		 */
        //g.setBackground(new Color(255, 0, 0, 127));
        g.setColor(new Color(0, 76, 64, 200));
        g.setStroke(new BasicStroke(0));
        g.fillRect(w/4, 0, w/2, h);

        g.setColor(new Color(255,255,255));
        Font font = new Font("Arial", Font.BOLD, 18);
        g.setFont(font);
        FontMetrics fm = g.getFontMetrics();
        int wfm = fm.stringWidth(this.args[6]);
        int hfm = fm.getHeight();
        g.rotate(Math.PI*0.5);
        g.drawString(this.args[6], h/2-wfm/2, -w/4-6);
        g.rotate((-1)*Math.PI*0.5);

        
        g.setColor(new Color(0,0,0, 255));  
        font = new Font("Arial", Font.BOLD, 9);
        g.setFont(font);
        fm = g.getFontMetrics();
        wfm = fm.stringWidth(this.args[3]);
        hfm = fm.getHeight();
        g.rotate(Math.PI*0.5);
        g.drawString(this.args[3], 0, -w+10);
        
        
        String data = "Data: " + this.args[4] + " - Hora: " + this.args[5];
        wfm = fm.stringWidth(data);
        hfm = fm.getHeight();
        g.drawString("Data: " + this.args[4] + " - Hora: " + this.args[5], h-wfm, -w+10);

        
        g.dispose();
        
        ImageIO.write(img, "png", bOut);
        
        Rectangle rectSign = new Rectangle(595-w-10, 842-h-120, w+1, h+1);
        Object[] r = new Object[2];
        r[0] = rectSign;
        r[1] = bOut.toByteArray();
        	
        return r;        
    }
    
    
    
    public void certProtocolo() throws IOException, GeneralSecurityException {
    	
    	for (int i = 0; i < this.args.length; i++) {
			System.out.println(i + " - " +this.args[i]);
		}
    	
    	PdfReader reader = new PdfReader(this.args[7]);
    	PdfDocument pdfDoc = new PdfDocument(reader);

    	//if (!this.isSigned(pdfDoc)) {
    	//	return "";
    	//}
    	
    	KeyStore ks = KeyStore.getInstance(KeyStore.getDefaultType());
        ks.load(new FileInputStream(this.args[8]), this.args[9].toCharArray());
        String alias = ks.aliases().nextElement();
        PrivateKey pk = (PrivateKey) ks.getKey(alias, this.args[9].toCharArray());
        Certificate[] chain = ks.getCertificateChain(alias);
    	
        reader = new PdfReader(this.args[7]);
        PdfSigner signer = new PdfSigner(
			reader, 
			new FileOutputStream("/home/leandro/TEMP/teste.pdf"), 
			new StampingProperties().useAppendMode());
        
        Object[] image = this.getImageRightSign();
        
        PdfSignatureAppearance appearance = signer.getSignatureAppearance();
        appearance
	        .setReason("Certificação de Protocolo")
	        .setLocation("CamaraJataiGoBR")
	        .setReuseAppearance(false)
	        .setPageRect((Rectangle) image[0])
	        .setPageNumber(1)
	        .setLayer2Text("Signed on " + new Date().toString())
	        .setRenderingMode(PdfSignatureAppearance.RenderingMode.GRAPHIC)
			.setSignatureGraphic(ImageDataFactory.create((byte[]) image[1]));
        
        
        
        
        
 
        PrivateKeySignature pks = new PrivateKeySignature(pk, DigestAlgorithms.SHA256, this.provider.getName());
        IExternalDigest digest = new BouncyCastleDigest();
        signer.setFieldName("DDE-PortalCMJ");
        signer.signDetached(digest, pks, chain, null, null, null, 0, PdfSigner.CryptoStandard.CMS);
    	
    	
		
    }
	
}
