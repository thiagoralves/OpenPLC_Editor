<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:exsl="http://exslt.org/common" xmlns:regexp="http://exslt.org/regular-expressions" xmlns:str="http://exslt.org/strings" xmlns:func="http://exslt.org/functions" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:cc="http://creativecommons.org/ns#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:svg="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:ns="beremiz" version="1.0" extension-element-prefixes="ns func exsl regexp str dyn" exclude-result-prefixes="ns func exsl regexp str dyn">
  <xsl:output method="xml"/>
  <xsl:variable name="hmi_elements" select="//svg:*[starts-with(@inkscape:label, 'HMI:')]"/>
  <xsl:variable name="widgetparams" select="ns:GetWidgetParams()"/>
  <xsl:variable name="indexed_hmitree" select="/.."/>
  <xsl:variable name="pathregex" select="'^([^\[,]+)(\[[^\]]+\])?([-.\d,]*)$'"/>
  <xsl:template mode="parselabel" match="*">
    <xsl:variable name="label" select="@inkscape:label"/>
    <xsl:variable name="id" select="@id"/>
    <xsl:variable name="description" select="substring-after($label,'HMI:')"/>
    <xsl:variable name="_args" select="substring-before($description,'@')"/>
    <xsl:variable name="args">
      <xsl:choose>
        <xsl:when test="$_args">
          <xsl:value-of select="$_args"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$description"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="_typefreq" select="substring-before($args,':')"/>
    <xsl:variable name="typefreq">
      <xsl:choose>
        <xsl:when test="$_typefreq">
          <xsl:value-of select="$_typefreq"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$args"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="freq" select="substring-after($typefreq,'|')"/>
    <xsl:variable name="_type" select="substring-before($typefreq,'|')"/>
    <xsl:variable name="type">
      <xsl:choose>
        <xsl:when test="$_type">
          <xsl:value-of select="$_type"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$typefreq"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:if test="$type">
      <widget>
        <xsl:attribute name="id">
          <xsl:value-of select="$id"/>
        </xsl:attribute>
        <xsl:attribute name="type">
          <xsl:value-of select="$type"/>
        </xsl:attribute>
        <xsl:if test="$freq">
          <xsl:if test="not(regexp:test($freq,'^[0-9]*(\.[0-9]+)?[smh]?'))">
            <xsl:message terminate="yes">
              <xsl:text>Widget id:</xsl:text>
              <xsl:value-of select="$id"/>
              <xsl:text> label:</xsl:text>
              <xsl:value-of select="$label"/>
              <xsl:text> has wrong syntax of frequency forcing </xsl:text>
              <xsl:value-of select="$freq"/>
            </xsl:message>
          </xsl:if>
          <xsl:attribute name="freq">
            <xsl:value-of select="$freq"/>
          </xsl:attribute>
        </xsl:if>
        <xsl:for-each select="str:split(substring-after($args, ':'), ':')">
          <arg>
            <xsl:attribute name="value">
              <xsl:value-of select="."/>
            </xsl:attribute>
          </arg>
        </xsl:for-each>
        <xsl:variable name="paths" select="substring-after($description,'@')"/>
        <xsl:for-each select="str:split($paths, '@')">
          <xsl:if test="string-length(.) &gt; 0">
            <path>
              <xsl:variable name="path_match" select="regexp:match(.,$pathregex)"/>
              <xsl:variable name="pathminmax" select="str:split($path_match[4],',')"/>
              <xsl:variable name="path" select="$path_match[2]"/>
              <xsl:variable name="path_accepts" select="$path_match[3]"/>
              <xsl:variable name="pathminmaxcount" select="count($pathminmax)"/>
              <xsl:attribute name="value">
                <xsl:value-of select="$path"/>
              </xsl:attribute>
              <xsl:if test="string-length($path_accepts)">
                <xsl:attribute name="accepts">
                  <xsl:value-of select="$path_accepts"/>
                </xsl:attribute>
              </xsl:if>
              <xsl:choose>
                <xsl:when test="$pathminmaxcount = 2">
                  <xsl:attribute name="min">
                    <xsl:value-of select="$pathminmax[1]"/>
                  </xsl:attribute>
                  <xsl:attribute name="max">
                    <xsl:value-of select="$pathminmax[2]"/>
                  </xsl:attribute>
                </xsl:when>
                <xsl:when test="$pathminmaxcount = 1 or $pathminmaxcount &gt; 2">
                  <xsl:message terminate="yes">
                    <xsl:text>Widget id:</xsl:text>
                    <xsl:value-of select="$id"/>
                    <xsl:text> label:</xsl:text>
                    <xsl:value-of select="$label"/>
                    <xsl:text> has wrong syntax of path section </xsl:text>
                    <xsl:value-of select="$pathminmax"/>
                  </xsl:message>
                </xsl:when>
              </xsl:choose>
              <xsl:if test="$indexed_hmitree">
                <xsl:choose>
                  <xsl:when test="regexp:test($path,'^\.[a-zA-Z0-9_]+$')">
                    <xsl:attribute name="type">
                      <xsl:text>PAGE_LOCAL</xsl:text>
                    </xsl:attribute>
                  </xsl:when>
                  <xsl:when test="regexp:test($path,'^[a-zA-Z0-9_]+$')">
                    <xsl:attribute name="type">
                      <xsl:text>HMI_LOCAL</xsl:text>
                    </xsl:attribute>
                  </xsl:when>
                  <xsl:otherwise>
                    <xsl:variable name="item" select="$indexed_hmitree/*[@hmipath = $path]"/>
                    <xsl:variable name="pathtype" select="local-name($item)"/>
                    <xsl:if test="$pathminmaxcount = 3 and not($pathtype = 'HMI_INT' or $pathtype = 'HMI_REAL')">
                      <xsl:message terminate="yes">
                        <xsl:text>Widget id:</xsl:text>
                        <xsl:value-of select="$id"/>
                        <xsl:text> label:</xsl:text>
                        <xsl:value-of select="$label"/>
                        <xsl:text> path section </xsl:text>
                        <xsl:value-of select="$pathminmax"/>
                        <xsl:text> use min and max on non mumeric value</xsl:text>
                      </xsl:message>
                    </xsl:if>
                    <xsl:if test="count($item) = 1">
                      <xsl:attribute name="index">
                        <xsl:value-of select="$item/@index"/>
                      </xsl:attribute>
                      <xsl:attribute name="type">
                        <xsl:value-of select="$pathtype"/>
                      </xsl:attribute>
                    </xsl:if>
                  </xsl:otherwise>
                </xsl:choose>
              </xsl:if>
            </path>
          </xsl:if>
        </xsl:for-each>
        <xsl:if test="svg:desc">
          <desc>
            <xsl:value-of select="svg:desc/text()"/>
          </desc>
        </xsl:if>
      </widget>
    </xsl:if>
  </xsl:template>
  <xsl:template mode="genlabel" match="arg">
    <xsl:text>:</xsl:text>
    <xsl:value-of select="@value"/>
  </xsl:template>
  <xsl:template mode="genlabel" match="path">
    <xsl:text>@</xsl:text>
    <xsl:value-of select="@value"/>
    <xsl:if test="string-length(@min)&gt;0 or string-length(@max)&gt;0">
      <xsl:text>,</xsl:text>
      <xsl:value-of select="@min"/>
      <xsl:text>,</xsl:text>
      <xsl:value-of select="@max"/>
    </xsl:if>
  </xsl:template>
  <xsl:template mode="genlabel" match="widget">
    <xsl:text>HMI:</xsl:text>
    <xsl:value-of select="@type"/>
    <xsl:apply-templates mode="genlabel" select="arg"/>
    <xsl:apply-templates mode="genlabel" select="path"/>
  </xsl:template>
  <xsl:variable name="_parsed_widgets">
    <xsl:apply-templates mode="parselabel" select="$hmi_elements"/>
  </xsl:variable>
  <xsl:variable name="parsed_widgets" select="exsl:node-set($_parsed_widgets)"/>
  <xsl:variable name="svg_widget" select="$parsed_widgets/widget[1]"/>
  <xsl:variable name="svg_widget_type" select="$svg_widget/@type"/>
  <xsl:variable name="svg_widget_path" select="$svg_widget/@path"/>
  <xsl:variable name="svg_widget_count" select="count($parsed_widgets/widget)"/>
  <xsl:template mode="replace_params" match="@* | node()">
    <xsl:copy>
      <xsl:apply-templates mode="replace_params" select="@* | node()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template mode="replace_params" match="arg"/>
  <xsl:template mode="replace_params" match="path"/>
  <xsl:template mode="replace_params" match="widget">
    <xsl:copy>
      <xsl:apply-templates mode="replace_params" select="@* | node()"/>
      <xsl:copy-of select="$widgetparams/*"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template xmlns="http://www.w3.org/2000/svg" mode="inline_svg" match="@*">
    <xsl:copy/>
  </xsl:template>
  <xsl:template xmlns="http://www.w3.org/2000/svg" mode="inline_svg" match="@inkscape:label[starts-with(., 'HMI:')]"/>
  <xsl:template mode="inline_svg" match="node()">
    <xsl:copy>
      <xsl:if test="@id = $svg_widget/@id">
        <xsl:variable name="substituted_widget">
          <xsl:apply-templates mode="replace_params" select="$svg_widget"/>
        </xsl:variable>
        <xsl:variable name="substituted_widget_ns" select="exsl:node-set($substituted_widget)"/>
        <xsl:variable name="new_label">
          <xsl:apply-templates mode="genlabel" select="$substituted_widget_ns"/>
        </xsl:variable>
        <xsl:attribute name="inkscape:label">
          <xsl:value-of select="$new_label"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates mode="inline_svg" select="@* | node()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="/">
    <xsl:comment>
      <xsl:text>Widget dropped in Inkscape from Beremiz</xsl:text>
    </xsl:comment>
    <xsl:choose>
      <xsl:when test="$svg_widget_count &lt; 1">
        <xsl:message terminate="yes">
          <xsl:text>No widget detected on selected SVG</xsl:text>
        </xsl:message>
      </xsl:when>
      <xsl:when test="$svg_widget_count &gt; 1">
        <xsl:message terminate="yes">
          <xsl:text>Multiple widget DnD not yet supported</xsl:text>
        </xsl:message>
      </xsl:when>
    </xsl:choose>
    <xsl:apply-templates mode="inline_svg" select="/"/>
  </xsl:template>
</xsl:stylesheet>
